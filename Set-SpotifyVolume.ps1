param([ValidateRange(1,30)][int]$WaitSeconds = 20)
$ErrorActionPreference = 'Stop'

# Adjust only the Spotify.exe Windows audio session. Never change the system volume
# or another application's session (in particular, the browser that plays JARVIS TTS).
$source = @'
using System;
using System.Runtime.InteropServices;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    void EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr devices);
    void GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
    void GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice device);
    void RegisterEndpointNotificationCallback(IntPtr client);
    void UnregisterEndpointNotificationCallback(IntPtr client);
}
[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    void Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object result);
    void OpenPropertyStore(int access, out IntPtr properties);
    void GetId(out IntPtr id);
    void GetState(out int state);
}
[ComImport, Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 {
    void GetAudioSessionControl(ref Guid sessionGuid, int flags, out IntPtr control);
    void GetSimpleAudioVolume(ref Guid sessionGuid, int flags, out IntPtr volume);
    void GetSessionEnumerator(out IAudioSessionEnumerator sessions);
    void RegisterSessionNotification(IntPtr notification);
    void UnregisterSessionNotification(IntPtr notification);
    void RegisterDuckNotification(IntPtr notification);
    void UnregisterDuckNotification(IntPtr notification);
}
[ComImport, Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator {
    void GetCount(out int count);
    void GetSession(int index, out IAudioSessionControl2 session);
}
[ComImport, Guid("F4B1A599-7266-4319-A8CA-E70ACB11E8CD"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 {
    void GetState(out int state);
    void GetDisplayName(out IntPtr name);
    void SetDisplayName([MarshalAs(UnmanagedType.LPWStr)] string name, ref Guid context);
    void GetIconPath(out IntPtr path);
    void SetIconPath([MarshalAs(UnmanagedType.LPWStr)] string path, ref Guid context);
    void GetGroupingParam(out Guid grouping);
    void SetGroupingParam(ref Guid grouping, ref Guid context);
    void RegisterAudioSessionNotification(IntPtr notification);
    void UnregisterAudioSessionNotification(IntPtr notification);
    void GetSessionIdentifier(out IntPtr identifier);
    void GetSessionInstanceIdentifier(out IntPtr identifier);
    void GetProcessId(out uint processId);
    void IsSystemSoundsSession();
    void SetDuckingPreference([MarshalAs(UnmanagedType.Bool)] bool optOut);
}
[ComImport, Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ISimpleAudioVolume {
    void GetMasterVolume(out float volume);
    void SetMasterVolume(float volume, ref Guid context);
    void GetMute(out bool muted);
    void SetMute([MarshalAs(UnmanagedType.Bool)] bool muted, ref Guid context);
}
public static class SpotifySessionVolume {
    public static bool Set(float level) {
        var enumerator = (IMMDeviceEnumerator)new MMDeviceEnumerator();
        IMMDevice device;
        enumerator.GetDefaultAudioEndpoint(0, 0, out device); // eRender, eConsole
        var iid = new Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F");
        object managerObject;
        device.Activate(ref iid, 23, IntPtr.Zero, out managerObject); // CLSCTX_ALL
        var manager = (IAudioSessionManager2)managerObject;
        IAudioSessionEnumerator sessions;
        manager.GetSessionEnumerator(out sessions);
        int count;
        sessions.GetCount(out count);
        bool changed = false;
        for (int i = 0; i < count; i++) {
            IAudioSessionControl2 session;
            sessions.GetSession(i, out session);
            int state;
            try { session.GetState(out state); } catch { continue; }
            if (state != 1) continue; // AudioSessionStateActive: wait for actual playback.
            uint pid;
            try { session.GetProcessId(out pid); } catch { continue; }
            if (pid == 0) continue;
            string processName;
            try { processName = System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; }
            catch { continue; }
            if (!String.Equals(processName, "Spotify", StringComparison.OrdinalIgnoreCase)) continue;
            var volume = (ISimpleAudioVolume)session;
            var context = Guid.Empty;
            volume.SetMasterVolume(level, ref context);
            changed = true;
        }
        return changed;
    }
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumerator { }
'@

# Avoid compiling the helper repeatedly in the same PowerShell process.
if (-not ('SpotifySessionVolume' -as [type])) {
    Add-Type -TypeDefinition $source -Language CSharp
}

$target = 0.45
$attempts = [Math]::Ceiling(($WaitSeconds * 1000) / 750)
for ($attempt = 0; $attempt -lt $attempts; $attempt++) {
    try {
        if ([SpotifySessionVolume]::Set($target)) {
            Write-Output ('Volume da sessão Spotify ajustado para {0:P0}.' -f $target)
            exit 0
        }
    } catch {
        # Spotify may not have created its audio session yet; retry briefly.
    }
    Start-Sleep -Milliseconds 750
}
Write-Output 'Não encontrei uma sessão de áudio ativa do Spotify. Se estiver usando o Spotify no navegador, ajuste o aplicativo Spotify no Mixer de volume do Windows.'
exit 2
