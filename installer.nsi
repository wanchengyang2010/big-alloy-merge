; 合成大YK (Big Alloy Merge) — v2.3.0.0 NSIS 安装器
; Trash Panda Q Opal
Unicode true

!include "MUI2.nsh"
!include "FileFunc.nsh"

; ---- 基本信息 ----
!define PRODUCT_NAME "Big Alloy Merge"
!define PRODUCT_NAME_CN "合成大YK"
!define PRODUCT_VERSION "2.3.0.0"
!define PRODUCT_PUBLISHER "Trash Panda Q Opal"
!define PRODUCT_EXE "Big_Alloy_Merge.exe"
!define DEBUG_PASSWORD "3919"

Name "${PRODUCT_NAME_CN} ${PRODUCT_VERSION}"
OutFile "D:\F15Game\dist\Big_Alloy_Merge_Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

; ---- 界面设置 ----
!define MUI_ABORTWARNING
!define MUI_ICON "theme.ico"
!define MUI_UNICON "theme.ico"

; ---- 页面 ----
!insertmacro MUI_PAGE_DIRECTORY
Page custom DebugPageCreate DebugPageLeave
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; ---- 变量 ----
Var DebugPassword
Var DebugError

; ---- 安装区段 ----
Section "Install"
    SetOutPath "$INSTDIR"

    ; 主程序
    File "dist\${PRODUCT_EXE}"

    ; ── 资源文件（EXE 同目录，用户可替换）──
    ; assets/
    SetOutPath "$INSTDIR\assets"
    File "assets\yk.png"
    File "assets\theme.png"
    File "assets\victory.mp3"
    ; images/
    SetOutPath "$INSTDIR\assets\images"
    File "assets\images\0.png"
    File "assets\images\1.png"
    File "assets\images\2.png"
    File "assets\images\3.png"
    File "assets\images\4.png"
    File "assets\images\5.png"
    File "assets\images\6.png"
    File "assets\images\7.png"
    File "assets\images\8.png"
    File "assets\images\9.png"
    File "assets\images\10.png"
    File "assets\images\11.png"
    File "assets\images\12.png"
    File "assets\images\13.png"
    File "assets\images\14.png"
    File "assets\images\15.png"
    File "assets\images\16.png"

    ; music/ 背景音乐 + 合成音效
    SetOutPath "$INSTDIR\music"
    File "music\Two Steps From Hell - Victory.mp3"
    File "music\Two Steps From Hell、Merethe Soltvedt - Impossible.mp3"
    File "music\TheFatRat - Unity.mp3"
    File "music\Çeşitli Sanatçılar - L'internationale.mp3"

    SetOutPath "$INSTDIR\music\游戏音效备选"
    File "music\游戏音效备选\doo-doo-hast.mp3"
    File "music\游戏音效备选\mystical-atmosphere-7.mp3"
    File "music\游戏音效备选\sigh-through-the-nose.mp3"
    File "music\游戏音效备选\cockroach-squeaks.mp3"
    File "music\游戏音效备选\duck-called-apple-phone-comes-with-sound-game-sound-alert.mp3"
    File "music\游戏音效备选\loud-squeak.mp3"
    File "music\游戏音效备选\virtuoso-swings-of-the-hussar-saber.mp3"
    File "music\游戏音效备选\the-sound-of-a-man-vomiting-cartoon.mp3"
    File "music\游戏音效备选\the-rough-squeak-of-a-child39s-pipe.mp3"
    File "music\游戏音效备选\big-guard-dog-barking.mp3"
    File "music\游戏音效备选\goat-bleats.mp3"
    File "music\游戏音效备选\neighing-horse.mp3"
    File "music\游戏音效备选\prehistoric-dinosaur-sound.mp3"
    File "music\游戏音效备选\baboon-voice-sound.mp3"
    File "music\游戏音效备选\snowball-throw.mp3"
    File "music\游戏音效备选\game-skills-release-archery.mp3"

    ; pictures/ 开屏图
    SetOutPath "$INSTDIR\pictures"
    File "pictures\newflash.jfif"

    ; 数据文件
    SetOutPath "$INSTDIR"
    File "highscore.txt"
    File "Messages.txt"
    File "elements.txt"
    File "theme.ico"
    File "icon.png"

    ; ── 源码（v2.3.0.0）──
    SetOutPath "$INSTDIR\source"
    File "main.py"
    File "constants.py"
    File "data.py"
    File "game.py"
    File "physics.py"
    File "renderer.py"
    File "modes.py"
    File "debug_panel.py"
    File "autoplay.py"
    File "updater.py"
    File "image_processor.py"
    File "tune_sweep.py"
    File "settings_ui.py"
    File "version.py"
    File "CLAUDE.md"
    File "CHANGELOG.md"
    File "PHYSICS.md"
    File "USER_GUIDE.md"

    ; 调试授权标记
    ${If} $DebugPassword == "${DEBUG_PASSWORD}"
        FileOpen $0 "$INSTDIR\debug_3919.ok" w
        FileWrite $0 "${DEBUG_PASSWORD}"
        FileClose $0
    ${EndIf}

    ; 卸载程序
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; 注册表
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "DisplayName" "${PRODUCT_NAME_CN} ${PRODUCT_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "DisplayIcon" '"$INSTDIR\${PRODUCT_EXE}"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "Publisher" "${PRODUCT_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
        "NoRepair" 1

    ; 快捷方式
    CreateDirectory "$SMPROGRAMS\${PRODUCT_PUBLISHER}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_PUBLISHER}\${PRODUCT_NAME_CN}.lnk" \
        "$INSTDIR\${PRODUCT_EXE}"
    CreateShortCut "$SMPROGRAMS\${PRODUCT_PUBLISHER}\卸载 ${PRODUCT_NAME_CN}.lnk" \
        "$INSTDIR\Uninstall.exe"
    CreateShortCut "$DESKTOP\${PRODUCT_NAME_CN}.lnk" \
        "$INSTDIR\${PRODUCT_EXE}"
SectionEnd

; ---- 卸载区段 ----
Section "Uninstall"
    Delete "$INSTDIR\${PRODUCT_EXE}"
    Delete "$INSTDIR\debug_3919.ok"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\highscore.txt"
    Delete "$INSTDIR\Messages.txt"
    Delete "$INSTDIR\elements.txt"
    Delete "$INSTDIR\theme.ico"
    Delete "$INSTDIR\icon.png"

    RMDir /r "$INSTDIR\assets"
    RMDir /r "$INSTDIR\music"
    RMDir /r "$INSTDIR\pictures"
    RMDir /r "$INSTDIR\source"
    RMDir "$INSTDIR"

    Delete "$SMPROGRAMS\${PRODUCT_PUBLISHER}\${PRODUCT_NAME_CN}.lnk"
    Delete "$SMPROGRAMS\${PRODUCT_PUBLISHER}\卸载 ${PRODUCT_NAME_CN}.lnk"
    RMDir "$SMPROGRAMS\${PRODUCT_PUBLISHER}"
    Delete "$DESKTOP\${PRODUCT_NAME_CN}.lnk"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

    ; 用户数据（可选，询问）
    MessageBox MB_YESNO|MB_ICONQUESTION "是否同时删除用户数据（存档、最高分、设置）？$\n$\n位置：$APPDATA\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}" IDNO skip_userdata
    RMDir /r "$APPDATA\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}"
    skip_userdata:
SectionEnd

; ---- 调试密码页面 ----
Function DebugPageCreate
    !insertmacro MUI_HEADER_TEXT "调试选项" "输入调试密码以启用开发者功能（可选）"

    nsDialogs::Create 1018
    Pop $0

    ${NSD_CreateLabel} 0 20u 100% 14u "调试密码（留空跳过，密码：3919）："
    Pop $0

    ${NSD_CreatePassword} 0 40u 200u 14u ""
    Pop $DebugPassword

    ${NSD_CreateLabel} 0 70u 100% 14u ""
    Pop $DebugError

    nsDialogs::Show
FunctionEnd

Function DebugPageLeave
    ${NSD_GetText} $DebugPassword $0
    ${If} $0 == ""
        StrCpy $DebugPassword ""
    ${ElseIf} $0 == "${DEBUG_PASSWORD}"
        StrCpy $DebugPassword "${DEBUG_PASSWORD}"
    ${Else}
        MessageBox MB_OK|MB_ICONEXCLAMATION "密码不正确，请留空跳过或输入正确密码。"
        Abort
    ${EndIf}
FunctionEnd
