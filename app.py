from flask import Flask, request, jsonify, make_response
from sloot_data import fetch_sloot_data, generate_random_addresses, level_mapping
from image_generator import generate_profile_image, generate_battle_image
import re
import os
import time

import logging
from logging.handlers import RotatingFileHandler
from logging.config import dictConfig


dictConfig({
        "version": 1,
        "disable_existing_loggers": False,  # 不覆盖默认配置
        "formatters": {  # 日志输出样式
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",  # 控制台输出
                "level": "DEBUG",
                "formatter": "default",
            },
            "log_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "default",   # 日志输出样式对应formatters
                "filename": "/home/ec2-user/logs/fs-app.log",  # 指定log文件目录
                "maxBytes": 20*1024*1024,   # 文件最大20M
                "backupCount": 10,          # 最多10个文件
                "encoding": "utf8",         # 文件编码
            },

        },
        "root": {
            "level": "DEBUG",  # # handler中的level会覆盖掉这里的level
            "handlers": ["console", "log_file"],
        },
    }
)


app = Flask(__name__)

game_state = {}

@app.route('/start', methods=['POST'])
def start():
    start = time.time()
    
    # Get the msg hash as player address
    signature_packet = request.json
    hash_data = signature_packet.get('untrustedData')['messageHash']   
    get_hash = time.time()
    print(f"get hash time:{get_hash - start}")
    
    # Fetch player sloot data and generate enemies (involve outer API)
    player_sloot = fetch_sloot_data(hash_data)
    fetchPlayer = time.time()
    
    enemies_sloot = [fetch_sloot_data(address) for address in generate_random_addresses(1)]
    fetchEnemy= time.time()

    print(f"fetch player sloot time:{fetchPlayer - get_hash}")
    print(f"fetch enemy sloot time:{fetchEnemy - fetchPlayer}")
    
    # Generate profile images and store URLs
    #s3_bucket_name = 'frame-survivor-jp'
    background_image_path = "./static/asset/profile_bg2.png"
    profile_pic_urls = [generate_profile_image(player_sloot, enemy, background_image_path) for enemy in enemies_sloot]
    fetchImg = time.time()
    print(f"fetch img time:{fetchImg - fetchEnemy}")
    
    # Storing game data as state for later use
    game_state[hash_data] = {
        'player_sloot': player_sloot,
        'enemies_sloot': enemies_sloot,
        'current_enemy_index': 0,
        'profile_pic_urls': profile_pic_urls,
    }
    
    # Generate Frame data
    response_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="fc:frame" content="vNext" />
        <meta property="fc:frame:post_url" content="http://vanishk.xyz/games/frame-survivor/explore" /> #需要后面做成一整个逻辑，通过["untrustedData"]["buttonIndex"]来识别功能
        <meta property="fc:frame:image" content="{profile_pic_urls[0]}" />
        <meta property="fc:frame:button:1" content="Previous Enemy" />
        <meta property="fc:frame:button:2" content="Battle" />
        <meta property="fc:frame:button:3" content="Next Enemy" />
    </head>
    </html>
    """
    
    end = time.time()
    print(f"total time:{end - start}")
    
    return make_response(response_html, 200)



# need to revise
"""
@app.route('/battle', methods=['POST'])
def battle():
    user_data = request.json
    user_address = user_data.get('address')
    
    # Retrieve the game state for the user
    if user_address in game_state:
        player_sloot = game_state[user_address]['player_sloot']
        current_enemy_index = game_state[user_address]['current_enemy_index']
        enemy_sloot = game_state[user_address]['enemies_sloot'][current_enemy_index]
        
        # Battle logic, compare player_sloot and enemy_sloot stats
        # ...
        
        # Update game state if needed (e.g., move to next enemy)
        # game_state[user_address]['current_enemy_index'] += 1
        
        # Return the result and update the frame  
        # ...
    
        # Generate battle image
        battle_image_url = generate_battle_image(player_sloot, enemy_sloot, 'battle_template_path')

        # Update the frame with the battle result
        return jsonify({
            'meta': [
                {'property': 'fc:frame:image', 'content': battle_image_url}
                # ... other meta tags for the battle result ...
                    ]
            else:
            return jsonify({'error': 'User state not found'}), 404
            })
"""

@app.route('/get_sloot', methods=['GET'])
def get_sloot():
    address = request.args.get('address')

    # Validation for Ethereum addresses
    if not address or not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return jsonify({'error': 'Invalid address provided'}), 400

    try:
        sloot_data = fetch_sloot_data(address)
        return jsonify(sloot_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#log_handler = RotatingFileHandler('/home/ec2-user/logs/fs-app.log', maxBytes=100000, backupCount=1)
#log_handler.setLevel(logging.DEBUG)
#app.logger.addHandler(log_handler)
"""   
@app.route('/test', methods=['POST'])
def test():
    app.logger.debug('Test route hit.')
    received_data = request.get_json() or request.data or request.form
    if isinstance(received_data, bytes):
        received_data = received_data.decode('utf-8')  # Decoding bytes to str
    app.logger.info('Received data: %s', received_data)

    # Process data (add any processing you do here)
    app.logger.debug('Processing data...')
    hash_data = received_data['untrustedData']['messageHash'] 
    app.logger.info('hash data: %s', hash_data)

    # Prepare response
    response_data = {'status': 'success', 'data': received_data}
    app.logger.debug('Sending response: %s', response_data)
    return jsonify(response_data)
    """