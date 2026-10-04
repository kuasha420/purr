#compdef purr tuki purr-install app-install

_purr() {
    local -a commands
    commands=(
        'mirror:Benchmark regional mirrors & tune ParallelDownloads for maximum download throughput'
        'mirrors:Benchmark regional mirrors (alias for mirror)'
        'diet:Audit heavyweight packages across RAM, KDE activity & atime to prune dormant software'
        'trim:Audit and prune dormant software (alias for diet)'
        'audit:Audit and prune dormant software (alias for diet)'
        'repair:Headlessly diagnose and repair crashing Android apps (messenger)'
        'fix:Headlessly diagnose and repair crashing Android apps (alias for repair)'
        'upgrade:Run universal system upgrade across Pacman, AUR, and Flatpaks'
        'update:Run universal system upgrade (alias for upgrade)'
        'up:Run universal system upgrade (alias for upgrade)'
        'self-update:Update Purr host binaries and assets from git or AUR'
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
                mirror|mirrors)
                    _arguments \
                        '1: :(status optimize rank check info)' \
                        '(-c --country)'{-c,--country}'[Comma-separated ISO country codes to benchmark (e.g. BD,IN,SG)]:' \
                        '(-l --limit)'{-l,--limit}'[Maximum number of mirrors to rank (default: 10)]:' \
                        '(-p --parallel)'{-p,--parallel}'[Concurrent parallel download streams (default: 5)]:' \
                        '(-y --yes)'{-y,--yes}'[Assume yes and execute non-interactively]' \
                        '--json[Output status or benchmark in JSON format]' \
                        '(-h --help)'{-h,--help}'[Show help message and exit]'
                    ;;
                diet|trim|audit)
                    _arguments \
                        '(-s --min-size)'{-s,--min-size}'[Minimum package size threshold in MB (default: 150)]:' \
                        '(-y --yes)'{-y,--yes}'[Automatically prune without interactive prompt]' \
                        '--json[Output machine-readable JSON array]' \
                        '(-h --help)'{-h,--help}'[Show help message and exit]'
                    ;;
                upgrade|update|up)
                    _arguments \
                        '--auto-sync[Automatically synchronize deployed subsystem recipes]' \
                        '--sync-subsystems[Automatically synchronize deployed subsystem recipes]' \
                        '--diet[Precede upgrade with dormancy audit to prune abandoned software]' \
                        '--mirrors[Precede upgrade with fresh regional mirror optimization]' \
                        '-y[Assume yes for all prompts]'
                    ;;
                repair|fix)
                    _arguments \
                        '(-f --force)'{-f,--force}'[Force reinstallation even if ABI matches]' \
                        '1: :(messenger)'
                    ;;
                recipe|recipes)
                    _arguments \
                        '1: :(list info apply sync doctor prune teardown)' \
                        '2: :(waydroid-native)'
                    ;;
                apk|android)
                    _arguments \
                        '1: :(repair install launch list certify session sync ui paste)'
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
