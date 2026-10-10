import os
import zipfile
import hashlib

def audit_archive(zip_path="data/raw/hvac_fdd_benchmark.zip"):
    if not os.path.exists(zip_path):
        print(f"ERROR: Archive not found at {zip_path}")
        return None

    file_size = os.path.getsize(zip_path)
    with open(zip_path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()

    print(f"Archive Path: {zip_path}")
    print(f"Archive Size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"SHA-256: {sha256}")

    members = []
    suspicious_items = []
    executable_exts = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.dll', '.so', '.dylib', '.vbs', '.js', '.bin'}
    archive_exts = {'.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz'}

    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()
        total_uncompressed = 0

        for info in infolist:
            total_uncompressed += info.file_size
            filename = info.filename
            ext = os.path.splitext(filename)[1].lower()
            
            # Security checks
            is_suspicious = False
            reasons = []
            if filename.startswith("/") or filename.startswith("\\") or (len(filename) > 1 and filename[1] == ":"):
                is_suspicious = True
                reasons.append("Absolute path")
            if ".." in filename:
                is_suspicious = True
                reasons.append("Directory traversal ('..')")
            if ext in executable_exts:
                is_suspicious = True
                reasons.append("Executable extension")
            if ext in archive_exts:
                is_suspicious = True
                reasons.append("Nested archive")
            
            if is_suspicious:
                suspicious_items.append((filename, reasons))

            members.append({
                "filename": filename,
                "size_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "ratio": (1 - info.compress_size / info.file_size) * 100 if info.file_size > 0 else 0,
                "extension": ext,
                "crc": info.CRC,
                "date_time": f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d} {info.date_time[3]:02d}:{info.date_time[4]:02d}:{info.date_time[5]:02d}"
            })

    print(f"\nTotal Members: {len(members)}")
    print(f"Total Uncompressed Size: {total_uncompressed} bytes ({total_uncompressed / (1024*1024):.2f} MB)")
    print(f"Suspicious files detected: {len(suspicious_items)}")
    for item, reasons in suspicious_items:
        print(f"  WARNING: {item} -> {', '.join(reasons)}")

    print("\nMember Details:")
    for m in members:
        print(f" - {m['filename']}: {m['size_bytes']:,} bytes (compressed: {m['compressed_bytes']:,} bytes, {m['ratio']:.1f}% reduction, ext: '{m['extension']}', modified: {m['date_time']})")

    return {
        "zip_path": zip_path,
        "file_size": file_size,
        "sha256": sha256,
        "total_uncompressed": total_uncompressed,
        "members": members,
        "suspicious_items": suspicious_items
    }

def extract_archive(zip_path="data/raw/hvac_fdd_benchmark.zip", target_dir="data/interim"):
    os.makedirs(target_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()
        for info in infolist:
            # Check against directory traversal or absolute path
            if info.filename.startswith(("/", "\\")) or ".." in info.filename:
                raise ValueError(f"Unsafe file path detected: {info.filename}")
            zf.extract(info, target_dir)
            print(f"Extracted: {info.filename} -> {os.path.join(target_dir, info.filename)}")

if __name__ == "__main__":
    audit = audit_archive()
    if audit and len(audit["suspicious_items"]) == 0:
        print("\nExtracting archive into data/interim/...")
        extract_archive()
        print("Extraction complete.")

