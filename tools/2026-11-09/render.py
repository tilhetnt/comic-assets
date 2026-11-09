import sys, asyncio
from playwright.async_api import async_playwright
async def main(html,out):
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={'width':1400,'height':800},device_scale_factor=1.5)
        await pg.goto('file://'+html); await pg.wait_for_timeout(800)
        await pg.evaluate("document.fonts.ready")
        dims=await pg.evaluate("[document.documentElement.scrollWidth,document.documentElement.scrollHeight, document.fonts.check('700 30px CN'), document.querySelector('.banner h1').getBoundingClientRect().width, document.querySelector('.banner img').getBoundingClientRect().left-document.querySelector('.banner h1').getBoundingClientRect().right, Array.from(document.querySelectorAll('.txt')).map(e=>Math.round(e.getBoundingClientRect().height))]")
        print('dims/font/title w/gap/card heights',dims)
        await pg.screenshot(path=out,full_page=True); await b.close()
asyncio.run(main(sys.argv[1],sys.argv[2]))
