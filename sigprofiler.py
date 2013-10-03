from __future__ import with_statement

import os
from optparse import OptionParser
import sys
import signal
from collections import defaultdict

_counter = defaultdict(int)
_cum_counter = defaultdict(int)
_outfile = None

__version__ = '0.0.3'

def _sig_handler(signal, frame):
    global _counter, _cum_counter
    code = frame.f_code
    key = (code, frame.f_lineno)
    _counter[key] += 1
    _cum_counter[key] += 1
    s = set()
    s.add(code)
    f = frame.f_back
    while f is not None:
        code = f.f_code
        if code not in s:
            _cum_counter[f.f_code, f.f_lineno] += 1
            s.add(code)
        f = f.f_back

def reset():
    _counter.clear()
    _cum_counter.clear()

def uninstall():
    for sig in (signal.ITIMER_PROF, signal.ITIMER_VIRTUAL, signal.ITIMER_REAL):
        handler = signal.gethandler(sig)
        if handler is _sig_handler:
            signal.sethandler(sig, signal.SIG_DFL)

def install(target='cpu', interval=0.01):
    reset()

    if target == 'cpu':
        ttype = signal.ITIMER_PROF
        sigtype = signal.SIGPROF
    elif target == 'user':
        ttype = signal.ITIMER_VIRTUAL
        sigtype = signal.SIGVTALRM
    elif target == 'real':
        ttype = signal.ITIMER_REAL
        sigtype = signal.SIGALRM

    signal.signal(sigtype, _sig_handler)
    signal.setitimer(ttype, interval, interval)

    if hasattr(signal, 'siginterrupt'):
        signal.siginterrupt(sigtype, False)


def _print_profile(counter, total, file):
    items = list(counter.items())
    items.sort(key=lambda x: x[1], reverse=True)
    basename = os.path.basename
    for code_line, count in items:
        code, lineno = code_line
        file.write(
                "%20s:%-4d %20s %f\n" % (
                basename(code.co_filename), lineno,
                code.co_name, 100.0*count/total)
                )

def _show_profile():
    if _outfile is None:
        file = sys.stderr
    else:
        file = open(_outfile, 'w')
    if file is None:
        file = sys.stderr
    total = sum(_counter.values())
    file.write("=== time ===\n")
    _print_profile(_counter, total, file)
    file.write("== cumulative time ==\n")
    _print_profile(_cum_counter, total, file)
    if _outfile is not None:
        file.close()

def _show_profile_handler(signal, frame):
    _show_profile()

def main():
    parser = OptionParser(usage="%prog [options] script [script options]")
    parser.allow_interspersed_args = False
    parser.add_option('-o', '--outfile',
            help="Save report to <outfile>", default=None)
    parser.add_option('-u', '--user1', help='Install USR1 signal handler',
            action='store_true', default=False)
    parser.add_option('-U', '--user2', help='Install USR2 signal handler',
            action='store_true', default=False)
    parser.add_option('-i', '--interval', type="float",
            help="Timer interval in seconds. (default: 0.05",
            default=0.01)
    parser.add_option('-t', '--timer',
            help="Timer type used.", choices=('cpu', 'user', 'real'),
            default='real')

    if not sys.argv[1:]:
        parser.print_usage()
        sys.exit(2)

    (options, args) = parser.parse_args()
    global _outfile
    _outfile = options.outfile

    if options.user1:
        signal.signal(signal.SIGUSR1, _show_profile_handler)
    if options.user2:
        signal.signal(signal.SIGUSR1, _show_profile_handler)

    install(options.timer, options.interval)

    import atexit
    atexit.register(_show_profile)

    if (len(args) > 0):
        progname = args[0]
        sys.argv[:] = args
        sys.path.insert(0, os.path.dirname(sys.argv[0]))
        import __main__
        d = dict(__file__=progname,
                 __name__='__main__',
                 )
        code = open(progname,'rb').read()
        code = compile(code, progname, 'exec')
        exec(code, d, d)
    else:
        parser.print_usage()
    return parser

if __name__ == '__main__':
    main()
