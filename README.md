# DMS Reporting

Refactor theo hướng doi tuong cho luong doc Excel CRM MISA va xuat bao cao doanh so khach hang.

## Chay CLI

```bash
python main.py --company abipha --start-date 2026-01-01 --end-date 2026-12-31
```

Lenh tren se tao 6 file Excel trong `modules/<company>/report/`:

- Bao cao doanh so khach hang tong hop
- Bao cao doanh so chi tiet theo nhom san pham
- Bao cao khach hang phat sinh doanh so lan dau
- Bao cao khach hang gan sai dia ban
- Bao cao nhan vien da nghi con trong file phan tuyen
- Bao cao khach hang con gan cho nhan vien da nghi viec

File `Bao cao khach hang phat sinh doanh so lan dau` co:

- Moi thang la 1 sheet rieng: `Thang 1`, `Thang 2`, ...
- Khach hang phat sinh lan dau trong thang nao chi nam o sheet thang do, khong lap lai o thang sau

Chi muon xuat rieng report sai dia ban:

```bash
python main.py --company abipha --territory-only
```

Lenh `--territory-only` se tao 3 file:

- Bao cao khach hang gan sai dia ban
- Bao cao nhan vien da nghi con trong file phan tuyen
- Bao cao khach hang con gan cho nhan vien da nghi viec

## Build Windows

Project da duoc chuan bi san de build `.exe` Windows voi ten phat hanh dep hon va co icon rieng.

Build local tren Windows:

```powershell
cd path\\to\\project
build_windows.bat
```

Build tu GitHub Actions:

- workflow: `.github/workflows/build-windows-exe.yml`
- artifact: `Abipha-DMS-Reporter-windows-x64`

Sau khi build xong:

- file chay nam tai `dist\\windows-package\\Abipha-DMS-Reporter.exe`
- file zip phat hanh nam tai `dist\\Abipha-DMS-Reporter-windows-x64.zip`
- script se copy ca thu muc `modules\\` vao cung goi phat hanh

## Bien moi truong cho API CRM

```bash
export MISA_CLIENT_ID=your_client_id
export MISA_CLIENT_SECRET=your_client_secret
```
