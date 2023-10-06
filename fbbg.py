from pathlib import Path
from subprocess import run
from lxml.html import fromstring as string2html
from lxml.html import tostring as html2string
import shlex
from datetime import datetime
from feedgen.feed import FeedGenerator
import pytz


FBBG_DOMAIN = "fbbg.example"


def render(root, path):
    print('** reading {}'.format(path))
    directory = path.parent
    command = 'pandoc --from=markdown+yaml_metadata_block+inline_notes --mathml --standalone {} --template={} --output={}'
    filename = '.'.join(path.name.split('.')[:-1]) + '.html'
    command = command.format(path, root / 'template.html', directory / filename)
    run(shlex.split(command))


def read(path):
    print('** reading {}'.format(path))
    with path.open('r') as f:
        html = f.read()
    html = string2html(html)

    try:
        title = html.xpath("//meta[@key='title']/@value")[0]
        date = html.xpath("//meta[@key='date']/@value")[0]
        abstract = html.xpath("//meta[@key='abstract']/@value")[0]
        date = datetime.fromisoformat(date)
        date = date.replace(tzinfo=pytz.UTC)
        body = html2string(html.xpath("//div[@id='root']")[0])
        return str(path.parent) + '/', title, date, abstract, body
    except Exception as exc:
        print("Ignoring '{}' failed to gather metadata because of the following error: {}".format(path, exc))
        now = datetime.now()
        now = now.replace(tzinfo=pytz.UTC)
        return path, None, now, None, None


def main():
    print('* converting md to html')
    root = Path('.')
    for path in root.rglob('**/index.md'):
        if str(path).startswith('.'):
            continue
        path = path.resolve()
        render(root, path)
    print('* gathering metadata')
    meta = []
    for path in root.rglob('**/index.html'):
        if str(path).startswith('.'):
            continue
        if str(path) == 'index.html':
            continue
        meta.append(read(path))
    meta.sort(key=lambda x: (x[2], x[1]), reverse=True)

    with open('header.md') as f:
        out = f.read()

    for path, title, date, abstract, _ in meta:
        out += "\n\n## [{}](/{})\n\n\n{}: {} \n\n".format(title, path, date.strftime("%Y-%m-%d"), abstract)

    print('* Creating index')
    with open('index.md', 'w') as f:
        f.write(out)
    render(root, Path('index.md').resolve())

    print('* Creating feeds')

    fg = FeedGenerator()
    fg.id('https://{}/'.format(FBBG_DOMAIN))
    fg.title(FBBG_DOMAIN)

    fg.link(href='https://{}/'.format(FBBG_DOMAIN), rel='alternate')
    fg.subtitle('Follow blog, blog good!')
    fg.language('en')

    for item in meta:
        path, title, date, abstract, body = item
        if not (path and title and date and abstract and body):
            print("Ooops with {}: {}".format(path, item))
            continue
        if not date:
            print("Ignoring {} because no date!".format(path))
            continue
        fe = fg.add_entry()
        url = 'https://{}/{}'.format(FBBG_DOMAIN, path)
        fe.id(url)
        fe.guid(url, permalink=True)
        fe.title(title)
        fe.link(href=url)
        fe.summary(abstract)
        fe.description(abstract)
        fe.published(date)
        fe.content(body, type='html')
    fg.atom_file('atom.xml')
    fg.rss_file('feed.xml')


if __name__ == '__main__':
    main()
