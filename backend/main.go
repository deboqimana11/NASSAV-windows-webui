package main

import (
	"database/sql"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type AppConfig struct {
	SavePath  string `json:"SavePath"`
	DBPath    string `json:"DBPath"`
	QueuePath string `json:"QueuePath"`
}

var (
	videoListCache []VideoItem
	cacheMutex     sync.RWMutex
	logger         = log.New(os.Stdout, "[NASSAV] ", log.LstdFlags|log.Lshortfile)
	projectRoot    string
	mediaPath      string
	databasePath   string
	queueFilePath  string
	workFilePath   string
	serverPort     string
	apiKey         string
	pythonCmd      string
)

type VideoItem struct {
	ID     string `json:"id"`
	Title  string `json:"title"`
	Poster string `json:"poster"`
}

type VideoDetail struct {
	ID          string   `json:"id"`
	Title       string   `json:"title"`
	ReleaseDate string   `json:"releaseDate"`
	Fanarts     []string `json:"fanarts"`
	VideoFile   string   `json:"videoFile,omitempty"`
}

type DownloadStatus struct {
	Active     bool     `json:"active"`
	Current    string   `json:"current"`
	Queue      []string `json:"queue"`
	QueueCount int      `json:"queueCount"`
}

type NfoFile struct {
	XMLName     xml.Name `xml:"movie"`
	Title       string   `xml:"title"`
	ReleaseDate string   `xml:"releasedate"`
	Premiered   string   `xml:"premiered"`
}

func enableCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Allow-Credentials", "true")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {
	projectRoot = findProjectRoot()
	config, err := loadAppConfig(projectRoot)
	if err != nil {
		logger.Fatalf("Failed to load config: %v", err)
	}

	mediaPath = resolvePath(projectRoot, firstNonEmpty(os.Getenv("NASSAV_MEDIA_PATH"), config.SavePath, "./videos"))
	databasePath = resolvePath(projectRoot, firstNonEmpty(os.Getenv("NASSAV_DB_PATH"), config.DBPath, "./db/downloaded.db"))
	queueFilePath = resolvePath(projectRoot, firstNonEmpty(os.Getenv("NASSAV_QUEUE_PATH"), config.QueuePath, "./db/download_queue.txt"))
	workFilePath = resolvePath(projectRoot, firstNonEmpty(os.Getenv("NASSAV_WORK_PATH"), "./work"))
	serverPort = normalizePort(firstNonEmpty(os.Getenv("NASSAV_SERVER_PORT"), "31471"))
	apiKey = firstNonEmpty(os.Getenv("NASSAV_API_KEY"), "IBHUSDBWQHJEJOBDSW")
	pythonCmd = defaultPythonCommand()
	if override := os.Getenv("NASSAV_PYTHON"); override != "" {
		pythonCmd = override
	}

	if err := os.MkdirAll(mediaPath, 0o755); err != nil {
		logger.Fatalf("Failed to create media path %s: %v", mediaPath, err)
	}
	if err := os.MkdirAll(filepath.Dir(databasePath), 0o755); err != nil {
		logger.Fatalf("Failed to create db directory %s: %v", filepath.Dir(databasePath), err)
	}
	if err := os.MkdirAll(filepath.Dir(queueFilePath), 0o755); err != nil {
		logger.Fatalf("Failed to create queue directory %s: %v", filepath.Dir(queueFilePath), err)
	}
	if err := ensureFile(queueFilePath); err != nil {
		logger.Fatalf("Failed to ensure queue file: %v", err)
	}
	if err := ensureFile(workFilePath); err != nil {
		logger.Fatalf("Failed to ensure work file: %v", err)
	}
	if err := ensureDownloadTable(databasePath); err != nil {
		logger.Printf("Ensure download table failed: %v", err)
	}

	logger.Printf("Starting server on port %s", serverPort)
	logger.Printf("Project root: %s", projectRoot)
	logger.Printf("Media path: %s", mediaPath)
	logger.Printf("Database path: %s", databasePath)

	if err := buildVideoListCache(); err != nil {
		logger.Fatalf("Failed to build initial cache: %v", err)
	}

	go startCacheUpdater(30 * time.Minute)

	mux := http.NewServeMux()
	mux.HandleFunc("/api/videos", listVideosHandler)
	mux.HandleFunc("/api/videos/", videoDetailHandler)
	mux.HandleFunc("/api/addvideo/", addVideoHandler)
	mux.HandleFunc("/api/status", downloadStatusHandler)
	mux.HandleFunc("/file/", imageHandler)

	handler := enableCORS(mux)
	logger.Fatal(http.ListenAndServe(":"+serverPort, handler))
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}

func normalizePort(port string) string {
	return strings.TrimPrefix(strings.TrimSpace(port), ":")
}

func defaultPythonCommand() string {
	candidates := []string{"python3", "python"}
	if runtime.GOOS == "windows" {
		candidates = []string{"python", "py"}
	}

	for _, candidate := range candidates {
		if _, err := exec.LookPath(candidate); err == nil {
			return candidate
		}
	}
	return candidates[0]
}

func findProjectRoot() string {
	if override := os.Getenv("NASSAV_PROJECT_ROOT"); override != "" {
		return override
	}

	candidates := []string{}
	if cwd, err := os.Getwd(); err == nil {
		candidates = append(candidates, cwd)
	}
	if exePath, err := os.Executable(); err == nil {
		candidates = append(candidates, filepath.Dir(exePath))
	}

	for _, candidate := range candidates {
		if root, ok := locateProjectRoot(candidate); ok {
			return root
		}
	}

	if len(candidates) > 0 {
		return candidates[0]
	}
	return "."
}

func locateProjectRoot(start string) (string, bool) {
	current := start
	for i := 0; i < 8; i++ {
		configPath := filepath.Join(current, "cfg", "configs.json")
		if _, err := os.Stat(configPath); err == nil {
			return current, true
		}
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
		current = parent
	}
	return "", false
}

func loadAppConfig(root string) (AppConfig, error) {
	configPath := filepath.Join(root, "cfg", "configs.json")
	content, err := os.ReadFile(configPath)
	if err != nil {
		return AppConfig{}, err
	}

	var config AppConfig
	if err := json.Unmarshal(content, &config); err != nil {
		return AppConfig{}, err
	}
	return config, nil
}

func resolvePath(root, raw string) string {
	if raw == "" {
		return root
	}
	if filepath.IsAbs(raw) {
		return filepath.Clean(raw)
	}
	return filepath.Clean(filepath.Join(root, raw))
}

func ensureFile(path string) error {
	file, err := os.OpenFile(path, os.O_CREATE, 0o644)
	if err != nil {
		return err
	}
	return file.Close()
}

func startCacheUpdater(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for range ticker.C {
		logger.Println("Starting scheduled cache update...")
		if err := buildVideoListCache(); err != nil {
			logger.Printf("Cache update failed: %v", err)
		} else {
			logger.Println("Cache updated successfully")
		}
	}
}

func buildVideoListCache() error {
	cacheMutex.Lock()
	defer cacheMutex.Unlock()

	startTime := time.Now()
	logger.Println("Building video list cache...")

	files, err := os.ReadDir(mediaPath)
	if err != nil {
		logger.Printf("Error reading directory %s: %v", mediaPath, err)
		return fmt.Errorf("read directory failed: %w", err)
	}

	type dirEntryWithInfo struct {
		entry os.DirEntry
		info  os.FileInfo
	}

	var dirs []dirEntryWithInfo
	for _, file := range files {
		if !file.IsDir() {
			continue
		}
		info, err := file.Info()
		if err != nil {
			logger.Printf("Error getting info for %s: %v", file.Name(), err)
			continue
		}
		dirs = append(dirs, dirEntryWithInfo{entry: file, info: info})
	}

	sort.Slice(dirs, func(i, j int) bool {
		return dirs[i].info.ModTime().After(dirs[j].info.ModTime())
	})

	validCount := 0
	for _, dir := range dirs {
		posterPath := filepath.Join(mediaPath, dir.entry.Name(), dir.entry.Name()+"-poster.jpg")
		if _, err := os.Stat(posterPath); err == nil {
			validCount++
		}
	}

	if validCount == len(videoListCache) {
		logger.Printf("Cache unchanged. Valid items: %d", validCount)
		return nil
	}

	videoListCache = nil

	var count int
	for _, dir := range dirs {
		videoID := dir.entry.Name()
		posterPath := filepath.Join(mediaPath, videoID, videoID+"-poster.jpg")

		if _, err := os.Stat(posterPath); err != nil {
			logger.Printf("Poster not found for %s: %v", videoID, err)
			continue
		}

		title, _, err := parseTitleAndDate(videoID)
		if err != nil {
			logger.Printf("Failed to parse NFO for %s: %v", videoID, err)
			title = videoID
		}

		videoListCache = append(videoListCache, VideoItem{
			ID:     videoID,
			Title:  title,
			Poster: fmt.Sprintf("/file/%s/%s-poster.jpg", videoID, videoID),
		})
		count++
	}

	logger.Printf("Cache built successfully. Items: %d, Duration: %v", count, time.Since(startTime))
	return nil
}

func parseTitleAndDate(videoID string) (title, releaseDate string, err error) {
	nfoPath := filepath.Join(mediaPath, videoID, videoID+".nfo")

	file, err := os.Open(nfoPath)
	if err != nil {
		return "", "", fmt.Errorf("open file failed: %w", err)
	}
	defer file.Close()

	decoder := xml.NewDecoder(file)
	decoder.CharsetReader = func(charset string, input io.Reader) (io.Reader, error) {
		return input, nil
	}

	var nfo NfoFile
	if err := decoder.Decode(&nfo); err != nil {
		return "", "", fmt.Errorf("xml decode failed: %w", err)
	}

	date := nfo.ReleaseDate
	if date == "" {
		date = nfo.Premiered
	}
	if nfo.Title == "" {
		nfo.Title = videoID
	}

	return nfo.Title, date, nil
}

func listVideosHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if err := buildVideoListCache(); err != nil {
		logger.Printf("List request cache refresh failed: %v", err)
	}

	cacheMutex.RLock()
	defer cacheMutex.RUnlock()

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	if err := json.NewEncoder(w).Encode(videoListCache); err != nil {
		logger.Printf("Error encoding video list: %v", err)
		httpError(w, "Internal server error", http.StatusInternalServerError)
	}
}

func videoDetailHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	videoID := strings.TrimPrefix(r.URL.Path, "/api/videos/")
	if videoID == "" {
		httpError(w, "Invalid video ID", http.StatusBadRequest)
		return
	}

	detail := VideoDetail{ID: videoID}
	startTime := time.Now()

	title, date, err := parseTitleAndDate(videoID)
	if err != nil {
		logger.Printf("NFO parse for %s failed: %v", videoID, err)
		detail.Title = videoID
		detail.ReleaseDate = "Unknown"
	} else {
		detail.Title = title
		detail.ReleaseDate = date
	}

	fanartDir := filepath.Join(mediaPath, videoID)
	if files, err := os.ReadDir(fanartDir); err == nil {
		type fanartFile struct {
			path   string
			num    int
			hasNum bool
		}

		var fanarts []fanartFile
		for _, file := range files {
			name := file.Name()
			if !file.IsDir() && strings.HasPrefix(name, videoID+"-fanart") && strings.HasSuffix(name, ".jpg") {
				parts := strings.Split(name, "-fanart")
				if len(parts) < 2 {
					continue
				}

				numPart := strings.TrimSuffix(parts[1], ".jpg")
				numPart = strings.TrimPrefix(numPart, "-")

				var num int
				var hasNum bool
				if n, err := strconv.Atoi(numPart); err == nil {
					num = n
					hasNum = true
				}

				fanarts = append(fanarts, fanartFile{
					path:   fmt.Sprintf("/file/%s/%s", videoID, name),
					num:    num,
					hasNum: hasNum,
				})
			}
		}

		sort.Slice(fanarts, func(i, j int) bool {
			if fanarts[i].hasNum && fanarts[j].hasNum {
				return fanarts[i].num < fanarts[j].num
			}
			if fanarts[i].hasNum && !fanarts[j].hasNum {
				return true
			}
			if !fanarts[i].hasNum && fanarts[j].hasNum {
				return false
			}
			return fanarts[i].path < fanarts[j].path
		})

		for _, f := range fanarts {
			detail.Fanarts = append(detail.Fanarts, f.path)
		}
	} else {
		logger.Printf("Error reading fanart dir for %s: %v", videoID, err)
	}

	videoFile := filepath.Join(mediaPath, videoID, videoID+".mp4")
	if _, err := os.Stat(videoFile); err == nil {
		detail.VideoFile = fmt.Sprintf("/file/%s/%s.mp4", videoID, videoID)
	}

	logger.Printf("Processed detail request for %s in %v", videoID, time.Since(startTime))

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	if err := json.NewEncoder(w).Encode(detail); err != nil {
		logger.Printf("Error encoding detail for %s: %v", videoID, err)
		httpError(w, "Internal server error", http.StatusInternalServerError)
	}
}

func downloadStatusHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	current := readCurrentWork(workFilePath)
	queue := sanitizeQueueItems(queueFilePath, current)
	status := DownloadStatus{
		Active:     current != "",
		Current:    current,
		Queue:      queue,
		QueueCount: len(queue),
	}

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	if err := json.NewEncoder(w).Encode(status); err != nil {
		logger.Printf("Error encoding status: %v", err)
		httpError(w, "Internal server error", http.StatusInternalServerError)
	}
}

func imageHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pathParts := strings.Split(strings.TrimPrefix(r.URL.Path, "/file/"), "/")
	if len(pathParts) < 2 {
		httpError(w, "Invalid image path", http.StatusBadRequest)
		return
	}

	videoID := pathParts[0]
	filename := strings.Join(pathParts[1:], "/")
	imagePath := filepath.Join(mediaPath, videoID, filename)

	if !strings.HasPrefix(filepath.Clean(imagePath), filepath.Clean(mediaPath)) {
		httpError(w, "Invalid path", http.StatusBadRequest)
		return
	}

	fileInfo, err := os.Stat(imagePath)
	if os.IsNotExist(err) {
		http.NotFound(w, r)
		return
	} else if err != nil {
		logger.Printf("Error accessing file %s: %v", imagePath, err)
		httpError(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	switch filepath.Ext(filename) {
	case ".jpg", ".jpeg":
		w.Header().Set("Content-Type", "image/jpeg")
	case ".png":
		w.Header().Set("Content-Type", "image/png")
	case ".mp4":
		w.Header().Set("Content-Type", "video/mp4")
	}

	logger.Printf("Serving file %s (Size: %d)", imagePath, fileInfo.Size())
	http.ServeFile(w, r, imagePath)
}

func addVideoHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		httpError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		http.Error(w, "Authorization header missing", http.StatusUnauthorized)
		return
	}
	if !strings.HasPrefix(authHeader, "Bearer ") {
		http.Error(w, "Invalid authorization format", http.StatusUnauthorized)
		return
	}

	token := strings.TrimPrefix(authHeader, "Bearer ")
	if token != apiKey {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	videoID := strings.TrimPrefix(r.URL.Path, "/api/addvideo/")
	if videoID == "" {
		httpError(w, "Invalid video ID", http.StatusBadRequest)
		return
	}

	id := strings.ToUpper(videoID)
	logger.Printf("Received ID: %s", id)

	db, err := sql.Open("sqlite3", databasePath)
	if err != nil {
		httpError(w, "Database open failed", http.StatusInternalServerError)
		logger.Printf("Open DB failed: %v", err)
		return
	}
	defer db.Close()

	exists, err := checkStringExists(db, id)
	if err != nil {
		logger.Printf("Query DB failed: %v", err)
		exists = checkVideoArtifacts(id)
		logger.Printf("Fallback artifact check for %s: %v", id, exists)
	}

	response := fmt.Sprintf("%s already downloaded", id)
	if !exists {
		response = fmt.Sprintf("Add %s to download queue", id)
		go func() {
			cmd := exec.Command(pythonCmd, "main.py", id)
			cmd.Dir = projectRoot
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr
			if err := cmd.Run(); err != nil {
				logger.Printf("command exec failed: %v", err)
			} else {
				logger.Printf("command exec succ")
			}
		}()
	}
	logger.Println(response)

	w.Header().Set("Content-Type", "text/plain")
	_, _ = w.Write([]byte(response))
}

func checkStringExists(db *sql.DB, target string) (bool, error) {
	if _, err := db.Exec("CREATE TABLE IF NOT EXISTS MissAV (bvid TEXT PRIMARY KEY)"); err != nil {
		return false, err
	}

	var exists bool
	query := "SELECT EXISTS(SELECT 1 FROM MissAV WHERE bvid = ? LIMIT 1)"
	err := db.QueryRow(query, target).Scan(&exists)
	return exists, err
}

func ensureDownloadTable(dbPath string) error {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec("CREATE TABLE IF NOT EXISTS MissAV (bvid TEXT PRIMARY KEY)")
	return err
}

func checkVideoArtifacts(videoID string) bool {
	videoDir := filepath.Join(mediaPath, videoID)
	mp4Path := filepath.Join(videoDir, videoID+".mp4")
	nfoPath := filepath.Join(videoDir, videoID+".nfo")

	if _, err := os.Stat(mp4Path); err == nil {
		return true
	}
	if _, err := os.Stat(nfoPath); err == nil {
		return true
	}
	return false
}

func readCurrentWork(path string) string {
	content, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	value := strings.TrimSpace(string(content))
	if value == "" || value == "0" || value == "1" {
		return ""
	}
	return strings.ToUpper(value)
}

func readQueueItems(path string) []string {
	content, err := os.ReadFile(path)
	if err != nil {
		return []string{}
	}
	lines := strings.Split(string(content), "\n")
	items := make([]string, 0, len(lines))
	for _, line := range lines {
		value := strings.TrimSpace(line)
		if value == "" {
			continue
		}
		items = append(items, strings.ToUpper(value))
	}
	return items
}

func sanitizeQueueItems(path string, current string) []string {
	items := readQueueItems(path)
	if len(items) == 0 {
		return []string{}
	}

	seen := make(map[string]bool)
	cleaned := make([]string, 0, len(items))
	for _, item := range items {
		if item == "" {
			continue
		}
		if current != "" && item == current {
			continue
		}
		if seen[item] {
			continue
		}
		if checkVideoArtifacts(item) {
			continue
		}
		seen[item] = true
		cleaned = append(cleaned, item)
	}

	if len(cleaned) != len(items) {
		content := strings.Join(cleaned, "\n")
		if content != "" {
			content += "\n"
		}
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			logger.Printf("Failed to rewrite queue file: %v", err)
		}
	}

	return cleaned
}

func httpError(w http.ResponseWriter, message string, code int) {
	logger.Printf("HTTP Error %d: %s", code, message)
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": message})
}

