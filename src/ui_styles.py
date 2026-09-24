SCROLLBAR_STYLE = '''
    QScrollBar:vertical {
        background: transparent; width: 4px; margin: 0; border: none;
    }
    QScrollBar:horizontal {
        background: transparent; height: 4px; margin: 0; border: none;
    }
    QScrollBar::handle:vertical {
        background: transparent; border-radius: 2px; min-height: 24px;
    }
    QScrollBar::handle:horizontal {
        background: transparent; border-radius: 2px; min-width: 24px;
    }
    QScrollBar::handle:hover { background: #aaaaaa; }
    QScrollBar::handle:pressed { background: #aaaaaa; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
'''
