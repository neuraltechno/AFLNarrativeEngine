import re
import urllib.request

def test():
    html = urllib.request.urlopen('https://afltables.com/afl/seas/2026.html').read().decode('utf-8')
    urls = re.findall(r'href="([^"]*/stats/games/[^"]+\.html)"', html)
    print(len(urls), urls[:3])

test()