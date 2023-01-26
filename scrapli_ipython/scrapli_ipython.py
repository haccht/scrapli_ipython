import sys
from io import BytesIO
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
        self._timeout = 30
        self._platform = ''
        self._connection = None

    def _connect(self, host, platform, username, password, transport, timeout, **kwargs):
        timeout  = timeout  or self._timeout
        platform = platform or self._platform

        if not platform:
            raise Exception(f"No platform specified")
        if not username:
            username = input("Username:")
        if not password:
            password = getpass("Password:")
        if transport == "ssh":
            transport = "ssh2"
        if transport not in ["ssh2", "telnet"]:
            raise Exception(f"Unknown transport: {transport}")

        self._connection = Scrapli(
                host=host,
                platform=platform,
                transport=transport,
                auth_username=username,
                auth_password=password,
                auth_strict_key=False,
                timeout_socket=timeout,
                timeout_transport=timeout,
                channel_log=ChannelLogIO(),
                **kwargs)
        self._connection.open()

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout',   type=int, default=30, nargs='?')
    @magic_arguments.argument('-p', '--platform',  type=str, default='', nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, default='', nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, default='', nargs='?')
    @magic_arguments.argument('-T', '--transport', type=str, default='ssh')
    @magic_arguments.argument('host', type=str)
    def scrapli(self, line):
        args = magic_arguments.parse_argstring(self.scrapli, line)
        self._connect(args.host, args.platform, args.username, args.password, args.transport, args.timeout)

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout',  type=int, default=30, nargs='?')
    @magic_arguments.argument('-p', '--platform', type=str, default='', nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, default='', nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, default='', nargs='?')
    @magic_arguments.argument('host', type=str)
    def ssh(self, line):
        args = magic_arguments.parse_argstring(self.ssh, line)
        self._connect(args.host, args.platform, args.username, args.password, "ssh", args.timeout)

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout',  type=int, default=30, nargs='?')
    @magic_arguments.argument('-p', '--platform', type=str, default='', nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, default='', nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, default='', nargs='?')
    @magic_arguments.argument('host', type=str)
    def telnet(self, line):
        args = magic_arguments.parse_argstring(self.telnet, line)
        self._connect(args.host, args.platform, args.username, args.password, "telnet", args.timeout)

    @line_magic
    def timeout(self, line):
        self._timeout = int(line)

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
    @magic_arguments.argument('-t', '--timeout', type=int, default=0, nargs='?')
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def cmd(self, line, cell):
        args = magic_arguments.parse_argstring(self.cmd, line)
        self._connection.get_prompt()
        resp = self._connection.send_commands(
                commands=self._format(cell),
                timeout_ops=args.timeout)
        if args.var:
            get_ipython().user_ns[args.var] = resp

    @cell_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, default=0, nargs='?')
    @magic_arguments.argument('-p', '--privilege', type=str, default='', nargs='?')
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def configure(self, line, cell):
        args = magic_arguments.parse_argstring(self.configure, line)
        self._connection.get_prompt()
        resp = self._connection.send_configs(
                configs=self._format(cell),
                privilege_level=args.privilege,
                timeout_ops=args.timeout)
        if args.var:
            get_ipython().user_ns[args.var] = resp


class ChannelLogIO(BytesIO):
    def write(self, b, **kwargs):
        sys.stdout.write(b.decode('utf-8', 'ignore'), **kwargs)


# monkey-patch scrapli.response.MultiResponse
def result_mp(self, separator: str = "-- \n") -> str:
    data = [f"{r.channel_input}\n{r.result}\n" for r in self.data]
    return separator.join(data)

setattr(MultiResponse, 'result', property(result_mp))
setattr(MultiResponse, 'result_mp', result_mp)
