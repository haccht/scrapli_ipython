from getpass import getpass
from jinja2 import Template
from scrapli import Scrapli
from scrapli.response import MultiResponse
from IPython.core import magic_arguments
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.core.getipython import get_ipython


@magics_class
class ScrapliMagics(Magics):
    def __init__(self, shell):
        super(ScrapliMagics, self).__init__(shell)
        self._platform = ''
        self._connection = None

    def _connect(self, host, platform, transport, **kwargs):
        platform = platform or self._platform
        if not platform:
            raise Exception(f"No platform specified")
        if transport not in ["ssh2", "telnet"]:
            raise Exception(f"Unknown transport: {transport}")

        self._connection = Scrapli(
                host=host,
                platform=platform,
                transport=transport,
                auth_username=input("Username:"),
                auth_password=getpass("Password:"),
                auth_strict_key=False,
                **kwargs)
        self._connection.open()

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-p', '--platform', type=str, default='', nargs='?')
    @magic_arguments.argument('-t', '--transport', type=str, default='ssh2')
    @magic_arguments.argument('host', type=str)
    def scrapli(self, line):
        args = magic_arguments.parse_argstring(self.scrapli, line)
        self._connect(args.host, args.platform, args.transport)

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-p', '--platform', type=str, default='', nargs='?')
    @magic_arguments.argument('host', type=str)
    def ssh(self, line):
        args = magic_arguments.parse_argstring(self.ssh, line)
        self._connect(args.host, args.platform, "ssh2")

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-p', '--platform', type=str, default='', nargs='?')
    @magic_arguments.argument('host', type=str)
    def telnet(self, line):
        args = magic_arguments.parse_argstring(self.telnet, line)
        self._connect(args.host, args.platform, "telnet")

    @line_magic
    def platform(self, line):
        self._platform = line.strip()

    @line_magic
    def connection(self, line):
        return self._connection

    @line_magic
    def close(self, line):
        self._connection.close()

    def _format(self, cell):
        cell = Template(cell).render(**get_ipython().user_ns)
        return [e for e in cell.splitlines() if e and not e.isspace()]

    @cell_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def cmd(self, line, cell):
        args = magic_arguments.parse_argstring(self.cmd, line)
        resp = self._connection.send_commands(self._format(cell))
        print(resp.result_mp())
        if args.var:
            get_ipython().user_ns[args.var] = resp

    @cell_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def configure(self, line, cell):
        args = magic_arguments.parse_argstring(self.cmd, line)
        resp = self._connection.send_configs(self._format(cell))
        print(resp.result_mp(separator=""))
        if args.var:
            get_ipython().user_ns[args.var] = resp


# monkey-patch scrapli.response.MultiResponse
def result_mp(self, separator: str ="-- \n") -> str:
    data = [f"{r.channel_input}\n{r.result}\n" for r in self.data]
    return separator.join(data)

setattr(MultiResponse, 'result', property(result_mp))
setattr(MultiResponse, 'result_mp', result_mp)
