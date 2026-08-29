#compdef purr tuki purr-install app-install

_purr() {
    local -a commands
    commands=(
        'upgrade:Run universal system upgrade across Pacman, AUR, and Flatpaks'
        'update:Run universal system upgrade (alias for upgrade)'
        'up:Run universal system upgrade (alias for upgrade)'
        'recipe:Manage reproducible ecosystem recipes (waydroid-native)'
        'apk:Manage Android packages, sessions, and device certification'
        'tray:Manage background system tray indicator'
        'integrate:Manage KDE Plasma desktop integrations (Favorites, Task Manager, Autostart)'
    )

    _arguments -C \
        '(-h --help)'{-h,--help}'[Show help message and exit]' \
        '(-v --version)'{-v,--version}'[Show version number and exit]' \
        '--dry-run[Search and resolve without installing]' \
        '--no-loop[Exit after single installation without session loop]' \
        '1: :->cmd' \
        '*:: :->args'

    case $state in
        cmd)
            _describe 'command' commands
            ;;
        args)
            case $line[1] in
                recipe|recipes)
                    _arguments \
                        '1: :(list info apply doctor prune teardown)' \
                        '2: :(waydroid-native)'
                    ;;
                apk|android)
                    _arguments \
                        '1: :(install launch list certify session sync ui paste)'
                    ;;
                tray)
                    _arguments \
                        '(-d --daemon)'{-d,--daemon}'[Run tray in background detached]' \
                        '(-i --interval)'{-i,--interval}'[Update check frequency in minutes (default: 60)]:' \
                        '--initial-delay[Initial check delay in seconds after boot/login (default: 15)]:' \
                        '(-h --help)'{-h,--help}'[Show help message and exit]'
                    ;;
                integrate)
                    _arguments \
                        '--all[Enable all KDE desktop integrations]' \
                        '--favorite[Add Purr to Kickoff favorites]' \
                        '--unfavorite[Remove Purr from Kickoff favorites]' \
                        '--pin[Pin Purr to KDE Task Manager]' \
                        '--unpin[Unpin Purr from KDE Task Manager]' \
                        '--tray[Start System Tray Indicator daemon]' \
                        '--start-tray[Start System Tray Indicator daemon]' \
                        '--restart-tray[Restart System Tray Indicator daemon]' \
                        '--autostart[Enable Autostart for Tray Indicator]' \
                        '--no-autostart[Disable Autostart for Tray Indicator]' \
                        '--status[Check current integration status]' \
                        '(-h --help)'{-h,--help}'[Show help message and exit]'
                    ;;
            esac
            ;;
    esac
}

_purr "$@"
