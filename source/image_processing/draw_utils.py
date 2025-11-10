# Author: HeartoLazor
# Description: Debug rendering utilities

from config.debug_config import DEBUG_CONFIG

def draw_debug_text(draw, frame_width, frame_height, text, font, text_align, font_color, font_background_color, offset_size):
    if font is None:
        return
    
    margin = DEBUG_CONFIG['text_margin']
    
    if text_align == 'bottom_left':
        text_position = (margin, frame_height - offset_size - margin)
        text_anchor = 'lt'
    elif text_align == 'bottom_right':
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_position = (frame_width - text_width - margin, frame_height - offset_size - margin)
        text_anchor = 'rt'
    elif text_align == 'top_left':
        text_position = (margin, margin)
        text_anchor = 'lt'
    elif text_align == 'top_right':
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_position = (frame_width - text_width - margin, margin)
        text_anchor = 'rt'
    else:
        text_position = (margin, frame_height - offset_size - margin)
        text_anchor = 'lt'
    
    if DEBUG_CONFIG['font_has_background']:
        bbox = draw.textbbox(text_position, text, font=font, anchor=text_anchor)
        if text_align == 'bottom_left':
            expanded_bbox = (
                bbox[0], bbox[1] - 1,
                bbox[2] - 1, bbox[3]
            )
        elif text_align == 'bottom_right':
            expanded_bbox = (
                bbox[0], bbox[1] - 1,
                bbox[2], bbox[3]
            )
        elif text_align == 'top_left':
            expanded_bbox = (
                bbox[0], bbox[1] - 1,
                bbox[2] - 1, bbox[3]
            )
        elif text_align == 'top_right':
            expanded_bbox = (
                bbox[0], bbox[1] - 1,
                bbox[2], bbox[3]
            )
        else:
            expanded_bbox = (
                bbox[0], bbox[1] - 1,
                bbox[2] - 1, bbox[3]
            )
        draw.rectangle(expanded_bbox, fill=font_background_color)
    
    draw.text(text_position, text, font=font, fill=font_color, anchor=text_anchor)