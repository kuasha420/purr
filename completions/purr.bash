# Bash completion for purr & tuki
_purr_completions() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    commands="upgrade update up recipe recipes apk android tray integrate help"
    opts="-h --help -v --version --dry-run --no-loop"

    if [[ ${COMP_CWORD} -eq 1 ]] ; then
        COMPREPLY=( $(compgen -W "${commands} ${opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "recipe" || "${prev}" == "recipes" ]] ; then
        local recipe_opts="list info apply doctor prune teardown waydroid-native"
        COMPREPLY=( $(compgen -W "${recipe_opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "apk" || "${prev}" == "android" ]] ; then
        local apk_opts="install launch list certify session sync ui"
        COMPREPLY=( $(compgen -W "${apk_opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "integrate" ]] ; then
        local int_opts="--all --favorite --unfavorite --pin --unpin --tray --autostart --no-autostart --status -h --help"
        COMPREPLY=( $(compgen -W "${int_opts}" -- ${cur}) )
        return 0
    fi

    if [[ "${prev}" == "tray" ]] ; then
        local tray_opts="--daemon -d -i --interval --initial-delay -h --help"
        COMPREPLY=( $(compgen -W "${tray_opts}" -- ${cur}) )
        return 0
    fi

    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _purr_completions purr tuki purr-install app-install
