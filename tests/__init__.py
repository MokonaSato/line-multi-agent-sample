# このファイルはtestsディレクトリをパッケージとして認識させるためのものです
import os
import sys

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
