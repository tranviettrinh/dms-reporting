# DMS Reporting

Refactor theo hướng doi tuong cho luong doc Excel CRM MISA va xuat bao cao doanh so khach hang.

## Chay app desktop tren macOS

Tu source:

```bash
python main_macos.py
```

Hoac:

```bash
python -m dms_reporting.macos_app
```

App desktop cho phep:

- Truong `Thư mục dữ liệu` mac dinh tro thang toi `modules/abipha`
- Mo app se vao 1 trang dang nhap rieng, dang nhap xong moi vao man hinh bao cao
- Dang nhap bang tai khoan noi bo de mo dung cac loai bao cao duoc cap quyen
- Tai khoan `user` chi nhin thay cac bao cao da duoc phan quyen
- Nhap `start date` va `end date`
- Tick chon tung loai bao cao can xuat file
- Chon rieng trang thai don ban ra va trang thai don tra lai
- Co nut chon nhanh `Chọn tất cả`, `Chỉ phân tuyến`, `Bỏ chọn`
- Cau hinh `Nguồn cập nhật` bang file `latest-macos.json` hoac URL HTTPS
- Kiem tra va cai ban `.app` moi ngay trong giao dien macOS
- Tab `Cập nhật` co them khu `Phân quyền tài khoản` chi hien voi admin de tao user, doi mat khau va gan quyen theo tung bao cao

Lan dau mo app, he thong tu tao tai khoan mac dinh:

- Username: `admin`
- Password: `admin123`

Tai khoan `admin` xem duoc tat ca loai bao cao. Sau khi dang nhap, admin co the vao tab `Cập nhật` de tao tai khoan `user` va tick chon tung loai bao cao duoc phep su dung.

Neu dong goi thanh `.app`, sau khi mo tren macOS hay chon lai `Thư mục dữ liệu` tro den thu muc project hien tai chua `modules/`.

## Chay app desktop tren Windows

Tu source tren Windows:

```powershell
python main_windows.py
```

Ban Windows dung chung giao dien desktop voi macOS de chay bao cao, dang nhap tai khoan va quan ly phan quyen. Phan tu cap nhat trong app hien chi ho tro ban macOS, nhung chuc nang xuat bao cao va mo thu muc ket qua van hoat dong tren Windows 10.

## Chay CLI

```bash
python main.py --company abipha --start-date 2026-01-01 --end-date 2026-12-31
```

Lenh tren se tao 7 file Excel trong `modules/<company>/report/`:

- Bao cao doanh so khach hang tong hop
- Bao cao doanh so chi tiet theo nhom san pham
- Bao cao doanh thu san luong san pham theo nhan vien
- Bao cao khach hang phat sinh doanh so lan dau
- Bao cao khach hang gan sai dia ban
- Bao cao nhan vien da nghi con trong file phan tuyen
- Bao cao khach hang con gan cho nhan vien da nghi viec

File `Bao cao doanh thu san luong san pham theo nhan vien`:

- Moi thang la 1 sheet rieng: `Thang 1`, `Thang 2`, ...
- Trong tung sheet, du lieu duoc gom theo tung nhan vien va tung san pham
- Loai bo cac don hang cua khach hang co danh dau `La nha phan phoi` trong danh sach customer
- Khong tinh dong khuyen mai co `don gia ban = 0`
- San luong thuan = so luong ban ra - so luong tra lai co `don gia ban > 0`
- Doanh thu thuan = doanh thu ban ra - doanh thu tra lai cua cac dong co `don gia ban > 0`

File `Bao cao khach hang phat sinh doanh so lan dau` co:

- Moi thang la 1 sheet rieng: `Thang 1`, `Thang 2`, ...
- Khach hang phat sinh lan dau trong thang nao chi nam o sheet thang do, khong lap lai o thang sau

Chi muon xuat rieng report sai dia ban:

```bash
python main.py --company abipha --territory-only
```

Lenh `--territory-only` se tao 6 file:

- Bao cao khach hang gan dung dia ban
- Bao cao khach hang gan sai dia ban
- Bao cao nhan vien da nghi con trong file phan tuyen
- Bao cao khach hang con gan cho nhan vien da nghi viec
- Bao cao khach hang gan dung dia ban Giao hang
- Bao cao khach hang sai dia ban Giao hang

Chon tung loai bao cao can xuat:

```bash
python main.py --company abipha --reports summary detail invoice-territory --start-date 2026-01-01 --end-date 2026-12-31
```

Gia tri hop le cho `--reports`:

- `summary`
- `detail`
- `employee-product`
- `first-sales`
- `invoice-territory`
- `correct-shipping-territory`
- `shipping-territory`

Gia tri `invoice-territory` se xuat 4 file:

- Bao cao khach hang gan dung dia ban
- Bao cao khach hang gan sai dia ban
- Bao cao nhan vien da nghi con trong file phan tuyen
- Bao cao khach hang con gan cho nhan vien da nghi viec

Chon trang thai don ban ra va don tra lai:

```bash
python main.py \
  --company abipha \
  --reports summary detail employee-product \
  --start-date 2026-01-01 \
  --end-date 2026-12-31 \
  --sales-order-statuses "Bản nháp" "Đề nghị ghi" "Đã ghi" "Từ chối" \
  --return-order-statuses "Bản nháp" "Đề nghị" "Đã duyệt" "Từ chối" "Đã lập chứng từ"
```

Mac dinh:

- Don ban ra: `Bản nháp`, `Đề nghị ghi`, `Đã ghi`, `Từ chối`
- Don tra lai: `Bản nháp`, `Đề nghị`, `Đã duyệt`, `Từ chối`, `Đã lập chứng từ`

Ghi chu:

- Neu file nguon co du lieu go nham `Bản pháp`, he thong se tu dong tinh chung vao nhom `Bản nháp`

## Build app `.app` cho macOS

```bash
./scripts/build_macos_app.sh
```

Script se:

- Cai `pyinstaller` neu chua co
- Build trong thu muc tam `/private/tmp` de tranh metadata cua File Provider
- Xuat ban `.app` sach mac dinh tai `~/Applications/DMS Reporting.app`
- Strip `xattr` va ky ad-hoc lai bundle sau khi copy ra vi tri cuoi
- Dong goi giao dien desktop, khong mo cua so terminal khi chay

Co the doi noi xuat bang bien moi truong:

```bash
OUTPUT_DIR="$HOME/Applications/Abipha Builds" ./scripts/build_macos_app.sh
```

Du lieu Excel van nam o thu muc project ben ngoai app. Sau khi mo app, chi can chon thu muc goc chua `modules/`.

## Build `.exe` cho Windows 10

Build local tren Windows:

```powershell
.\build_windows.ps1
```

Hoac:

```cmd
build_windows.bat
```

Script se:

- Tao `.venv-build` neu chua co
- Cai dependency va chay `pytest`
- Dong goi GUI desktop thanh `dist\windows-package\DMS Reporting.exe`
- Copy thu muc `modules\` canh file `.exe`
- Tao goi `dist\dms-reporting-windows-x64.zip`

Mac dinh app se uu tien tim du lieu tai thu muc `modules\abipha` dat canh file `.exe`, nen goi artifact tu GitHub Actions co the chay tren Windows 10 sau khi giai nen.

## Build bang GitHub Actions Windows

Workflow moi:

- File: `.github/workflows/build-windows-app.yml`
- Runner: `windows-latest`
- Trigger: `workflow_dispatch`, `push` vao `main`, `pull_request`
- Artifact: `dms-reporting-windows-x64`

Artifact upload len Actions gom:

- `dist/windows-package/`
- `dist/dms-reporting-windows-x64.zip`

## Dong goi goi cap nhat cho app macOS

Sau khi build xong app moi, co the tao goi cap nhat `.zip` va manifest `latest-macos.json`:

```bash
./scripts/build_macos_update_artifacts.sh
```

Script mac dinh:

- Lay app tu `~/Applications/DMS Reporting.app`
- Tao file zip tai `releases/macos/DMS Reporting-<version>-macos.zip`
- Tao manifest tai `releases/macos/latest-macos.json`
- Dat `download_url` trong manifest theo duong dan tuong doi canh file manifest, nen co the dat ca 2 file tren o cung mot thu muc chia se noi bo

Neu muon manifest tro thang toi URL public:

```bash
DOWNLOAD_URL="https://example.com/DMS%20Reporting-0.2.0-macos.zip" ./scripts/build_macos_update_artifacts.sh
```

Neu muon them ghi chu phat hanh:

```bash
NOTES_FILE=release-notes.txt ./scripts/build_macos_update_artifacts.sh
```

Trong app, truong `Nguồn cập nhật` chap nhan:

- Duong dan local toi `latest-macos.json`
- URL HTTPS toi file manifest

Khi app dang chay tu `DMS Reporting.app`, nut `Cài bản mới` se tai goi `.zip`, giai nen va cai de bundle cu. Sau khi app dong, mo lai `DMS Reporting.app` de vao ban moi.

## Bien moi truong cho API CRM

```bash
export MISA_CLIENT_ID=your_client_id
export MISA_CLIENT_SECRET=your_client_secret
```
