import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'outputs', 'surfit_visualization');

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.webm': 'video/webm',
};

function serveStatic(port = 8792) {
  const server = createServer(async (req, res) => {
    try {
      let reqPath = (req.url || '/').split('?')[0];
      if (reqPath === '/') reqPath = '/visualization/index.html';
      const safePath = path.normalize(reqPath).replace(/^\.+/, '');
      const filePath = path.join(root, safePath);
      const ext = path.extname(filePath);
      const body = await readFile(filePath);
      res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
      res.end(body);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
    }
  });

  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true, channel: 'chrome', args: ['--autoplay-policy=no-user-gesture-required'] });
  } catch {
    return await chromium.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  }
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const server = await serveStatic(8792);
  const browser = await launchBrowser();

  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    const page = await context.newPage();
    page.setDefaultTimeout(240000);

    await page.goto('http://127.0.0.1:8792/visualization/index.html', { waitUntil: 'networkidle' });
    await page.waitForFunction(() => typeof window.renderWebMDataURL === 'function');

    const dataUrl = await page.evaluate(async () => {
      // @ts-ignore
      return await window.renderWebMDataURL();
    });

    const base64 = String(dataUrl).split(',')[1] || '';
    const outFile = path.join(outDir, 'surfit-visualization-162s.webm');
    await writeFile(outFile, Buffer.from(base64, 'base64'));

    console.log(`Exported: ${outFile}`);
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
