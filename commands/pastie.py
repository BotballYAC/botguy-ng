## pastie_pub.py [python]
#!/usr/bin/python
# Python API for pastie.org and commandline paster
# (c) 2009 Hector Martin <marcan@marcansoft.com>
# Released under the terms of the GNU General Public License, version 2 or 3

try:
    import urllib.request as urllib
except:
    import urllib

DEFAULT_NAME=None

class Pastie(object):
    def __init__(self, body='', parser=None, private=True, name = None):
        self.body = body
        self.parser = parser
        self.private = private
        self.name = name
    def submit(self):
        form = {
            "paste[parser]": self.parser or 'plain_text',
            "paste[body]": self.body,
            "paste[authorization]": 'burger',
            "paste[restricted]": self.private and '1' or '0'
        }
        if self.name is not None:
            form['paste[display_name]'] = self.name
        f = urllib.urlopen("http://pastie.org/pastes", urllib.parse.urlencode(form))
        f.close()
        return f.geturl()

if __name__ == '__main__':
    import sys, os
    from optparse import OptionParser
    
    extmap = {
        'as': 'actionscript',
        'c': 'c++',
        'cpp': 'c++',
        'c++': 'c++',
        'cxx': 'c++',
        'cc': 'c++',
        'h': 'c++',
        'hpp': 'c++',
        'h++': 'c++',
        'hxx': 'c++',
        'hc': 'c++',
        'css': 'css',
        'diff': 'diff',
        'patch': 'diff',
        'erb': 'html_rails',
        'rhtml': 'html_rails',
        'html': 'html',
        'htm': 'html',
        'java': 'java',
        'js': 'javascript',
        'm': 'objective-c++',
        'pas': 'pascal',
        'pl': 'perl',
        'php': 'php',
        'phtml': 'php',
        'php3': 'php',
        'php4': 'php',
        'php5': 'php',
        'py': 'python',
        'rb': 'ruby',
        'sh': 'bash',
        'sql': 'sql',
        'yml': 'yaml'
    }
    
    pastie = Pastie(body='', name=DEFAULT_NAME)
    parser = OptionParser()
    parser.add_option("-p", "--public", dest='private', action='store_false', help="make pastie public")
    parser.add_option("--private", dest='private', action='store_true', help="make pastie private (default)")
    parser.add_option("-n", "--name", dest='name', action='store', type='string', help="author of the pastie", metavar="NAME")
    parser.add_option("-t", "--type", dest='parser', action='store', type='string', help="file type (parser)", metavar="PARSER")

    args = parser.parse_args(sys.argv[1:], pastie)[1]
    
    if pastie.parser and '.' in pastie.parser:
        try:
            pastie.parser = extmap[pastie.parser.split('.')[-1].lower()]
        except:
            pastie.parser = None
    
    first_parser = None

    if len(args) == 0:
        pastie.body = sys.stdin.read()
    else:
        for name in args:
            if name == '-':
                body = sys.stdin.read()
                name = 'stdin'
            else:
                body = open(name, 'r').read()
                name = os.path.basename(name)
            try:
                parser = extmap[name.split('.')[-1].lower()]
                if first_parser is None:
                    first_parser = parser
            except:
                parser = 'plain_text'
            pastie.body += '## %s [%s]\n'%(name, pastie.parser or parser)
            pastie.body += body
            if pastie.body[-1] != '\n':
                pastie.body += '\n'
    if pastie.parser is None and first_parser is not None:
        pastie.parser = first_parser
    print(pastie.submit())

