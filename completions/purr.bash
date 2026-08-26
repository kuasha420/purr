# Bash completion for purr
_purr_completions() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="tray integrate help"
    opts="-h --help -v --version --dry-run --no-loop"

    if [[ ${COMP_CWORD} -eq 1 ]] ; then
        COMPREPLY=( $(compgen -W "${commands} ${opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "integrate" ]] ; then
        local int_opts="--all --favorite --unfavorite --pin --unpin --tray --autostart --no-autostart --status"
        COMPREPLY=( $(compgen -W "${int_opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "tray" ]] ; then
        COMPREPLY=( $(compgen -W "--daemon -d" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _purr_completions purr tuki purr-install app-install
