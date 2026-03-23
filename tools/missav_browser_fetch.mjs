import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const args = process.argv.slice(2);
const options = {};
for (let i = 0; i < args.length; i += 1) {
  const key = args[i];
  const value = args[i + 1];
  if (key.startsWith('--')) {
    options[key.slice(2)] = value;
  }
}

if (!options.url) {
  console.error('Missing --url');
  process.exit(2);
}

const timeoutMs = Number(options.timeoutMs || 180000);
const userDataDir = options.userDataDir || path.resolve('.browser-profile', 'missav');
const outputPath = options.output || '';
const proxyServer = options.proxy || '';
const avid = (options.avid || '').toLowerCase();
const origin = new URL(options.url).origin;

const launchOptions = {
  headless: false,
  viewport: { width: 1400, height: 900 },
  args: ['--disable-blink-features=AutomationControlled']
};

if (proxyServer) {
  launchOptions.proxy = { server: proxyServer };
}

const context = await chromium.launchPersistentContext(userDataDir, launchOptions);
const page = context.pages()[0] || await context.newPage();

const safePageTitle = async () => {
  try {
    return await page.title();
  } catch (error) {
    if ((error?.message || '').includes('Execution context was destroyed')) {
      await page.waitForLoadState('domcontentloaded').catch(() => {});
      return await page.title().catch(() => '');
    }
    return '';
  }
};

const getHtml = async () => {
  try {
    return await page.content();
  } catch (error) {
    if ((error?.message || '').includes('Execution context was destroyed')) {
      await page.waitForLoadState('domcontentloaded').catch(() => {});
      return await page.content().catch(() => '');
    }
    return '';
  }
};

const isChallenge = async () => (await safePageTitle()).toLowerCase().includes('just a moment');
const isPlayableDetail = async () => {
  const html = await getHtml();
  const title = await safePageTitle();
  if (title.includes('404') || html.includes('找不到页面')) return false;
  if (html.includes('og:title') && !html.includes('MissAV | 免费高清AV在线看')) {
    return true;
  }
  return html.includes('m3u8|') || html.includes('/playlist.m3u8') || html.includes('hlsUrl');
};

const waitUntilSolved = async () => {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (!await isChallenge()) return true;
    await page.waitForTimeout(1000);
  }
  return false;
};

const searchForAvid = async () => {
  await page.goto(`${origin}/cn`, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await waitUntilSolved();

  const searchUrl = `${origin}/cn/search/${encodeURIComponent(avid)}`;
  await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  if (await isChallenge()) {
    await waitUntilSolved();
  }

  const directLink = await page.evaluate((targetAvid) => {
    const anchors = Array.from(document.querySelectorAll('a[href]'));
    const target = targetAvid.toLowerCase();
    const matches = anchors
      .map((a) => a.href)
      .filter((href) => href.toLowerCase().includes(target) && !href.toLowerCase().includes('/search/'));
    return matches[0] || '';
  }, avid);

  if (directLink) {
    await page.goto(directLink, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    if (await isChallenge()) {
      await waitUntilSolved();
    }
    return;
  }

  const input = page.locator('[x-ref="search"]').first();
  if (await input.count()) {
    await input.fill(avid);
    await input.press('Enter');
    await page.waitForLoadState('domcontentloaded').catch(() => {});
    if (await isChallenge()) {
      await waitUntilSolved();
    }
  }
};

try {
  await page.goto(options.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
} catch (error) {
  console.error(`goto failed: ${error.message}`);
}

if (await isChallenge()) {
  await waitUntilSolved();
}

if (!(await isPlayableDetail()) && avid) {
  await searchForAvid();
}

const html = await getHtml();
if (outputPath) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, html, 'utf8');
}

console.log(html);
const success = await isPlayableDetail();
await context.close();
process.exit(success ? 0 : 1);
