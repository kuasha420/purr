#compdef purr tuki purr-install app-install

_purr() {
    local -a commands
    commands=(
        'upgrade:Run universal system upgrade across Pacman, AUR, and Flatpaks'
        'update:Run universal system upgrade (alias for upgrade)'
        'up:Run universal system upgrade (alias for upgrade)'
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
