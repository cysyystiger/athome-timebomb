from collections import Counter

def ref(msg, data):
    n = len(data.player)
    c = Counter(data.cutcard)
    if msg == '炸彈':
        return 3 #TextSendMessage(txt='遊戲結束，紅軍獲勝')
    elif len(data.allcard) == n+1 and msg == '安全引線':
        return 2 #TextSendMessage(txt='遊戲結束，紅軍獲勝')
    elif len(data.allcard) == n+1 and msg == '解除引線':
        return 1 #TextSendMessage(txt='遊戲結束，藍軍獲勝')
    elif c['解除引線'] == n-1 and msg == '解除引線':
        return 1 #TextSendMessage(txt='遊戲結束，藍軍獲勝')
    else:
        return 0
