import requests
import webbrowser
import json
import os

# 存储 token 和实例认证信息的文件路径
data_file = 'instances_data.json'

# 加载已存储的实例信息
def load_instances():
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    return {}

# 保存新的实例信息（client_id 和 client_secret）
def save_instance_data(instances_data):
    with open(data_file, 'w') as f:
        json.dump(instances_data, f)

# 向 Mastodon 实例注册应用
def register_app(mastodon_instance, instances_data):
    # 检查该实例是否已经注册
    if mastodon_instance in instances_data:
        print(f"{mastodon_instance} 已经注册过应用，跳过注册过程。")
        return instances_data[mastodon_instance]['client_id'], instances_data[mastodon_instance]['client_secret']

    # 如果没有注册过，则进行注册
    app_url = f'https://{mastodon_instance}/api/v1/apps'
    
    data = {
        'client_name': 'UPDATE AVATAR',  # 您应用的名称
        'redirect_uris': 'urn:ietf:wg:oauth:2.0:oob',  # 设置回调 URL
        'scopes': 'read write follow',  # 请求的权限
        # 'website': 'https://yourappwebsite.com'  # 您应用的官网（可选）
    }

    response = requests.post(app_url, data=data)
    
    if response.status_code == 200:
        app_info = response.json()
        client_id = app_info['client_id']
        client_secret = app_info['client_secret']
        print(f"应用注册成功！client_id: {client_id}, client_secret: {client_secret}")
        
        # 保存注册信息到实例数据
        instances_data[mastodon_instance] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': None  # 初始化为空，待获取
        }
        save_instance_data(instances_data)
        return client_id, client_secret
    else:
        print(f"应用注册失败: {response.status_code}, {response.text}")
        return None, None

# 从存储的实例数据文件中获取 token，如果文件不存在或 token 过期，则返回 None
def load_token(mastodon_instance, instances_data):
    if mastodon_instance in instances_data and 'access_token' in instances_data[mastodon_instance]:
        return instances_data[mastodon_instance]['access_token']
    return None

# 将新的 token 保存到实例数据
def save_token(mastodon_instance, access_token, instances_data):
    if mastodon_instance not in instances_data:
        instances_data[mastodon_instance] = {}

    instances_data[mastodon_instance]['access_token'] = access_token
    save_instance_data(instances_data)

# 检查令牌是否有效
def is_token_valid(mastodon_instance, access_token):
    check_url = f"https://{mastodon_instance}/api/v1/accounts/verify_credentials"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 启用 SSL 验证，默认配置
    response = requests.get(check_url, headers=headers, verify=True)  # 启用 SSL 验证

    if response.status_code == 200:
        return True  # 令牌有效
    elif response.status_code == 401:
        print(f"{mastodon_instance} 的访问令牌已被吊销或无效。")
        return False  # 令牌无效
    else:
        print(f"检查令牌有效性时发生错误: {response.status_code}, {response.text}")
        return False

# 一键更新头像
def update_avatar_for_instance(mastodon_instance, client_id, client_secret, instances_data, image_path):
    print(f"正在更新 {mastodon_instance} 的头像...")

    # 检查是否已有有效的 access_token
    access_token = load_token(mastodon_instance, instances_data)
    if access_token:
        print(f"{mastodon_instance} 使用已保存的访问令牌进行更新...")
    else:
        print(f"{mastodon_instance} 没有有效的访问令牌，开始授权流程...")

        # 构建授权 URL
        auth_url = f"https://{mastodon_instance}/oauth/authorize?client_id={client_id}&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&scope=read+write+follow"
        print(f"请访问以下链接并授权：{auth_url}")

        # 自动打开浏览器，让用户授权
        webbrowser.open(auth_url)

        # 提示用户在浏览器中获取授权码并输入
        code = input(f"请输入 {mastodon_instance} 授权后的授权码：")

        # 交换授权码为访问令牌
        token_url = f"https://{mastodon_instance}/oauth/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
        }

        response = requests.post(token_url, data=data)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens['access_token']
            print(f"{mastodon_instance} 访问令牌获取成功！")
            # 保存新的访问令牌
            save_token(mastodon_instance, access_token, instances_data)
        else:
            print(f"{mastodon_instance} 获取令牌失败: {response.status_code}, {response.text}")
            return

    # 更新头像 API 地址
    update_avatar_url = f"https://{mastodon_instance}/api/v1/accounts/update_credentials"

    # 打开图片并以二进制方式上传
    with open(image_path, 'rb') as image_file:
        files = {'avatar': image_file}
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.patch(update_avatar_url, headers=headers, files=files)

    if response.status_code == 200:
        print(f"{mastodon_instance} 头像更新成功！")
    else:
        print(f"{mastodon_instance} 头像更新失败: {response.status_code}, {response.text}")

# 主流程：用户输入实例 URL 和头像路径，然后更新头像
def main():
    # 获取用户输入
    mastodon_instance = input("请输入 Mastodon 实例的 URL（如 mastodon.social）：")
    image_path = input("请输入头像图片的路径：")

    # 加载已存储的实例数据
    instances_data = load_instances()

    # 注册应用并更新头像
    client_id, client_secret = register_app(mastodon_instance, instances_data)
    if client_id and client_secret:
        update_avatar_for_instance(
            mastodon_instance=mastodon_instance,
            client_id=client_id,
            client_secret=client_secret,
            instances_data=instances_data,
            image_path=image_path
        )

    # 保存更新后的实例数据
    save_instance_data(instances_data)

# 执行主流程
if __name__ == "__main__":
    main()
