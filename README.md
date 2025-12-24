# update_mastodon_avatar
更新Mastodon用户头像的脚本
## update_any_instance_avatar.py
此脚本实现更新某个实例头像
```
python update_any_instance_avatar.py
```
运行后需要输入实例url和头像图片路径，脚本自动打浏览器获取授权，获取完成后，将浏览器中的授权码粘贴到命令行中。授权失效自动重新获取。

## one_key_update_all_instance_avatar.py
此脚本实现更新脚本中全部实例头像，需提前编辑脚本中的实例地址和头像图片地址。
```
python one_key_update_all_instance_avatar.py
```
脚本自动打浏览器获取授权，获取完成后，将浏览器中的授权码粘贴到命令行中。授权失效自动重新获取。
