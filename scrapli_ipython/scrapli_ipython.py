import re
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
        self._scrapli_timeout = 30
        self._scrapli_platform = None
        self._scrapli_connection = None

    def _connect(
            self,
            host,
            platform,
            transport,
            username,
            password,
            timeout,
            **kwargs):
        platform = platform or self._scrapli_platform
        if platform is None:
            raise Exception(f"No platform specified")

        if transport == "ssh":
            transport = "ssh2"
        if transport not in ["ssh2", "telnet"]:
            raise Exception(f"Unknown transport: {transport}")

        if timeout is None:
            timeout = self._scrapli_timeout

        self._scrapli_connection = Scrapli(
            host=host,
            platform=platform,
            transport=transport,
            auth_username=username or input("Username:"),
            auth_password=password or getpass("Password:"),
            auth_strict_key=False,
            timeout_socket=timeout,
            timeout_transport=timeout,
            channel_log=ChannelLogIO(),
            **kwargs)
        self._scrapli_connection.open()

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, nargs='?')
    @magic_arguments.argument('-p', '--platform', type=str, nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, nargs='?')
    @magic_arguments.argument('-T', '--transport', type=str, choices=['ssh', 'telnet'], default='ssh')
    @magic_arguments.argument('host', type=str)
    def scrapli(self, line):
        args = magic_arguments.parse_argstring(self.scrapli, line)
        self._connect(
            args.host,
            args.platform,
            args.transport,
            args.username,
            args.password,
            args.timeout)

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, nargs='?')
    @magic_arguments.argument('-p', '--platform', type=str, nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, nargs='?')
    @magic_arguments.argument('host', type=str)
    def ssh(self, line):
        args = magic_arguments.parse_argstring(self.ssh, line)
        self._connect(
            args.host,
            args.platform,
            'ssh',
            args.username,
            args.password,
            args.timeout)

    @line_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, nargs='?')
    @magic_arguments.argument('-p', '--platform', type=str, nargs='?')
    @magic_arguments.argument('-U', '--username', type=str, nargs='?')
    @magic_arguments.argument('-P', '--password', type=str, nargs='?')
    @magic_arguments.argument('host', type=str)
    def telnet(self, line):
        args = magic_arguments.parse_argstring(self.telnet, line)
        self._connect(
            args.host,
            args.platform,
            'telnet',
            args.username,
            args.password,
            args.timeout)

    @line_magic
    def timeout(self, line):
        self._scrapli_timeout = int(line)

    @line_magic
    def platform(self, line):
        self._scrapli_platform = line.strip()

    @line_magic
    def connection(self, line):
        return self._scrapli_connection

    @line_magic
    def close(self, line):
        self._scrapli_connection.close()

    def _format(self, cell):
        ipython = get_ipython()
        if ipython:
            cell = Template(cell).render(**ipython.user_ns)

        return [
            line
            for line in cell.splitlines()
            if line and not re.match(r'^\s*(#.*)?$', line)]

    @cell_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, default=0, nargs='?')
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def cmd(self, line, cell):
        ipython = get_ipython()
        args = magic_arguments.parse_argstring(self.cmd, line)
        self._scrapli_connection.get_prompt()
        resp = self._scrapli_connection.send_commands(
            commands=self._format(cell),
            timeout_ops=args.timeout)
        if ipython and args.var:
            ipython.user_ns[args.var] = resp

    @cell_magic
    @magic_arguments.magic_arguments()
    @magic_arguments.argument('-t', '--timeout', type=int, default=0, nargs='?')
    @magic_arguments.argument('-p', '--privilege', type=str, default='', nargs='?')
    @magic_arguments.argument('var', type=str, default='', nargs='?')
    def configure(self, line, cell):
        ipython = get_ipython()
        args = magic_arguments.parse_argstring(self.configure, line)
        self._scrapli_connection.get_prompt()
        resp = self._scrapli_connection.send_configs(
            configs=self._format(cell),
            privilege_level=args.privilege,
            timeout_ops=args.timeout)
        if ipython and args.var:
            ipython.user_ns[args.var] = resp


class ChannelLogIO(BytesIO):
    def write(self, b, **kwargs):
        sys.stdout.write(b.decode('utf-8', 'ignore'), **kwargs)


# monkey-patch scrapli.response.MultiResponse
def result_mp(self, separator: str = "-- \n") -> str:
    data = [f"{r.channel_input}\n{r.result}\n" for r in self.data]
    return separator.join(data)


setattr(MultiResponse, 'result', property(result_mp))
setattr(MultiResponse, 'result_mp', result_mp)
