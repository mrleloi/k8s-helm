#!/bin/bash

# Đi đến thư mục gốc chứa các repositories con
cd /www/wwwroot/leloi
cd helm-charts
#cd docker-images

# Khởi tạo git nếu chưa có
#git init

# Lặp qua mỗi thư mục con
for d in */ ; do
    # Chỉ xử lý nếu đây là một git repository
    if [ -d "$d/.git" ]; then
        cd /www/wwwroot/leloi/helm-charts/"$d"
        # Lấy remote URL của repository hiện tại
        remote_url=$(git config --get remote.origin.url)
        # Lấy tên nhánh hiện tại
        current_branch=$(git rev-parse --abbrev-ref HEAD)
        # Trở về thư mục gốc
        cd /www/wwwroot/leloi
        # Thêm repository như một submodule
        git submodule add "$remote_url" "$d"
    fi
done

# Thêm, commit và push các thay đổi
git add .
git commit -m "Thêm các submodules"