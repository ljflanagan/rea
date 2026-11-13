// Rasterise sheet SVGs to PNG with the Playwright Chromium, when available.
// usage: node svg2png.cjs <width_px> <file.svg> [...]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [width, ...files] = process.argv.slice(2);
  const browser = await chromium.launch();
  for (const f of files) {
    const page = await browser.newPage({ deviceScaleFactor: 1 });
    await page.goto('file://' + path.resolve(f));
    const box = await page.evaluate(() => {
      const vb = document.documentElement.viewBox.baseVal; return [vb.width, vb.height];
    });
    const w = parseInt(width, 10), h = Math.round(w * box[1] / box[0]);
    await page.setViewportSize({ width: w, height: h });
    await page.evaluate(([w, h]) => {
      const s = document.documentElement; s.setAttribute('width', w); s.setAttribute('height', h);
    }, [w, h]);
    await page.screenshot({ path: f.replace(/\.svg$/, '.png') });
    await page.close();
  }
  await browser.close();
})().catch(e => { console.error(String(e)); process.exit(1); });
