"""Windows Credential Manager access (no API secrets in settings or logs)."""
import ctypes
import os
from ctypes import wintypes

TARGET = "JarvisVoiceStudio/OpenAI"
CRED_TYPE_GENERIC, CRED_PERSIST_LOCAL_MACHINE = 1, 2

class CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

def _api():
    if os.name != "nt": raise OSError("Windows Credential Manager só está disponível no Windows.")
    return ctypes.windll.advapi32

def save(secret: str) -> None:
    api = _api(); api.CredWriteW.argtypes=[ctypes.POINTER(CREDENTIAL),wintypes.DWORD];api.CredWriteW.restype=wintypes.BOOL;data = secret.encode("utf-16-le")
    blob = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    c = CREDENTIAL(0, CRED_TYPE_GENERIC, TARGET, None, wintypes.FILETIME(), len(data),
                   ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte)), CRED_PERSIST_LOCAL_MACHINE,
                   0, None, None, "JARVIS Voice Studio")
    if not api.CredWriteW(ctypes.byref(c), 0): raise ctypes.WinError()

def load() -> str:
    ptr = ctypes.POINTER(CREDENTIAL)()
    api=_api();api.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(ctypes.POINTER(CREDENTIAL))];api.CredReadW.restype=wintypes.BOOL;api.CredFree.argtypes=[ctypes.c_void_p]
    if not api.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(ptr)):
        return ""
    try:
        c = ptr.contents
        return ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize).decode("utf-16-le")
    finally: ctypes.windll.advapi32.CredFree(ptr)

def delete() -> None:
    api=_api();api.CredDeleteW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD];api.CredDeleteW.restype=wintypes.BOOL
    if not api.CredDeleteW(TARGET, CRED_TYPE_GENERIC, 0):
        code = ctypes.GetLastError()
        if code != 1168: raise ctypes.WinError(code)
