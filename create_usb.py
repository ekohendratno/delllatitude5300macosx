import os, sys, tempfile, shutil, subprocess, ctypes

def run(args, stream=False):
    if stream:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out = []
        for line in iter(p.stdout.readline, b''):
            line = line.decode('utf-8', errors='replace').rstrip()
            print(line)
            out.append(line)
        p.wait()
        return "\n".join(out), p.returncode
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.decode('utf-8', errors='replace'), p.returncode

def check_admin():
    import ctypes
    return ctypes.windll.shell32.IsUserAnAdmin() != 0

def elevate():
    import ctypes
    if not check_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def main():
    elevate()
    
    base_dir = os.path.dirname(os.path.realpath(__file__))
    gib_dir = os.path.join(base_dir, "gibMacOS")
    pkg = os.path.join(base_dir, "macOS_Install", "InstallAssistant.pkg")
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    dd_exe = os.path.join(gib_dir, "Scripts", "ddrelease64.exe")
    efi_src = os.path.join(base_dir, "EFI")
    
    temp_dir = tempfile.mkdtemp()
    
    print("=== Step 1: Check disk ===")
    out, rc = run([seven_zip, "l", "-txar", pkg])
    print("Xar listing done")
    
    print("\n=== Step 2: Extract SharedSupport.dmg ===")
    run([seven_zip, "e", "-txar", pkg, "*.dmg", "-o{}".format(temp_dir), "-y"], stream=True)
    
    ss_dmg = None
    for f in os.listdir(temp_dir):
        if f.lower().endswith(".dmg"):
            ss_dmg = os.path.join(temp_dir, f)
            print("Found: {}".format(f))
            break
    
    if not ss_dmg:
        print("ERROR: SharedSupport.dmg not found!")
        return
    
    print("\n=== Step 3: Extract BaseSystem.dmg ===")
    run([seven_zip, "e", ss_dmg, "*/Base*.dmg", "-o{}".format(temp_dir), "-y"], stream=True)
    
    base_dmg = None
    for f in os.listdir(temp_dir):
        if f.lower().startswith("base") and f.lower().endswith(".dmg"):
            base_dmg = os.path.join(temp_dir, f)
            print("Found: {}".format(f))
            break
    
    if not base_dmg:
        print("ERROR: BaseSystem.dmg not found!")
        return
    
    # Delete non-Base files
    for f in os.listdir(temp_dir):
        fpath = os.path.join(temp_dir, f)
        if fpath != base_dmg:
            os.remove(fpath)
    
    print("\n=== Step 4: Extract HFS image ===")
    run([seven_zip, "e", "-tdmg", base_dmg, "*.hfs", "-o{}".format(temp_dir), "-y"], stream=True)
    
    hfs_file = None
    for f in os.listdir(temp_dir):
        if f.lower().endswith(".hfs"):
            hfs_file = os.path.join(temp_dir, f)
            print("Found: {}".format(f))
            break
    
    if not hfs_file:
        print("ERROR: .hfs file not found!")
        return
    
    size_gb = os.path.getsize(hfs_file) / (1024**3)
    print("HFS size: {:.2f} GB".format(size_gb))
    
    print("\n=== Step 5: Write HFS image to partition 2 ===")
    dd_target = r"\\.\Harddisk1\Partition2"
    print("Writing to: {}".format(dd_target))
    run([dd_exe, "if={}".format(hfs_file), "of={}".format(dd_target), "bs=8M", "--progress"], stream=True)
    
    print("\n=== Step 6: Copy EFI to partition 1 (E:) ===")
    efi_target = r"E:\EFI"
    if os.path.exists(efi_target):
        shutil.rmtree(efi_target)
    shutil.copytree(efi_src, efi_target)
    print("EFI copied!")
    
    print("\n=== DONE! USB installer is ready ===")
    
    shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    main()