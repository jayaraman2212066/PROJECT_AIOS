#!/bin/bash
# JOK-AI-OS Welcome Banner
if [ -n "$PS1" ] && [ -z "$JOK_WELCOMED" ]; then
    export JOK_WELCOMED=1
    echo -e "\e[1;36m"
    cat << 'EOF'
     ██╗ ██████╗ ██╗  ██╗       █████╗ ██╗      ██████╗ ███████╗
     ██║██╔═══██╗██║ ██╔╝      ██╔══██╗██║     ██╔═══██╗██╔════╝
     ██║██║   ██║█████═╝ █████╗███████║██║     ██║   ██║███████╗
██   ██║██║   ██║██╔═██╗ ╚════╝██╔══██║██║     ██║   ██║╚════██║
╚█████╔╝╚██████╔╝██║ ╚██╗      ██║  ██║██║     ╚██████╔╝███████║
 ╚════╝  ╚═════╝ ╚═╝  ╚═╝      ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝
EOF
    echo -e "\e[0m\e[1;32m JOK-AI-OS 1.0 (Autonomous AI Edition) | Kernel $(uname -r)\e[0m"
    echo -e "\e[1;33m J0K AI ASSISTANT : Active and Online | Local Qwen 2.5 3B AI Brain\e[0m"
    echo -e "\e[37m Type your commands or press the floating 'J' star button on your desktop.\e[0m\n"
fi
