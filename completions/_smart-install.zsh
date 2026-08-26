#compdef smart-install app-install

_smart_install() {
    local -a opts
    opts=(
        '(-h --help)'{-h,--help}'[Show help message and exit]'
        '(-v --version)'{-v,--version}'[Show version number and exit]'
        '--dry-run[Search and resolve without installing]'
        '--no-loop[Exit after single installation without session loop]'
        '*:query: '
    )
    _arguments -s $opts
}

_smart_install "$@"
