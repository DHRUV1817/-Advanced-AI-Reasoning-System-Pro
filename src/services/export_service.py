"""
Conversation export service supporting multiple formats
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Union
from src.models.entry import ConversationEntry
from src.config.settings import AppConfig
from src.utils.logger import logger
from src.utils.helpers import sanitize_filename


class ConversationExporter:
    """
    📤 MULTI-FORMAT CONVERSATION EXPORTER
    """
    
    def __init__(self):
        self.export_dir = AppConfig.EXPORT_DIR
        self.backup_dir = AppConfig.BACKUP_DIR
        self.export_dir.mkdir(exist_ok=True, parents=True)
        self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def export_to_json(self, conversations: List[ConversationEntry], 
                       include_metadata: bool = True) -> str:
        """
        📄 EXPORT TO JSON
        """
        if include_metadata:
            data = [conv.to_dict() for conv in conversations]
        else:
            data = [
                {
                    'user': conv.user_message,
                    'assistant': conv.assistant_response,
                    'timestamp': conv.timestamp
                }
                for conv in conversations
            ]
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def export_to_markdown(self, conversations: List[ConversationEntry],
                          include_metadata: bool = True) -> str:
        """
        📝 EXPORT TO MARKDOWN
        """
        lines = [
            "# Conversation Export",
            f"\n**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Conversations:** {len(conversations)}\n",
            "---\n"
        ]
        
        for idx, conv in enumerate(conversations, 1):
            lines.append(f"## Conversation {idx}\n")
            
            if include_metadata:
                lines.append(f"**Timestamp:** {conv.timestamp}  ")
                lines.append(f"**Model:** {conv.model}  ")
                lines.append(f"**Reasoning Mode:** {conv.reasoning_mode}  ")
                lines.append(f"**Tokens Used:** {conv.tokens_used}  ")
                lines.append(f"**Inference Time:** {conv.inference_time:.2f}s\n")
            
            lines.append(f"**👤 User:**\n{conv.user_message}\n")
            lines.append(f"**🤖 Assistant:**\n{conv.assistant_response}\n")
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def export_to_txt(self, conversations: List[ConversationEntry],
                     include_metadata: bool = True) -> str:
        """
        📄 EXPORT TO PLAIN TEXT
        """
        lines = [
            "=" * 80,
            "CONVERSATION EXPORT",
            f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Conversations: {len(conversations)}",
            "=" * 80,
            ""
        ]
        
        for idx, conv in enumerate(conversations, 1):
            lines.append(f"\n{'=' * 80}")
            lines.append(f"CONVERSATION {idx}")
            lines.append(f"{'=' * 80}")
            
            if include_metadata:
                lines.append(f"Timestamp: {conv.timestamp}")
                lines.append(f"Model: {conv.model}")
                lines.append(f"Reasoning Mode: {conv.reasoning_mode}")
                lines.append(f"Tokens Used: {conv.tokens_used}")
                lines.append(f"Inference Time: {conv.inference_time:.2f}s")
                lines.append("")
            
            lines.append(f"USER:\n{conv.user_message}\n")
            lines.append(f"ASSISTANT:\n{conv.assistant_response}\n")
        
        return "\n".join(lines)
    
    def export_to_pdf(self, conversations: List[ConversationEntry],
                     include_metadata: bool = True,
                     title: str = "Conversation Export",
                     subtitle: Optional[str] = None,
                     author: Optional[str] = None) -> Optional[str]:
        """
        📄 EXPORT TO PDF — Premium design with proper page breaking

        Returns the string path for compatibility with Gradio (or None on error).
        """
        if not AppConfig.ENABLE_PDF_EXPORT:
            logger.warning("⚠️ PDF export is disabled")
            return None

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                PageBreak,
            )
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            logger.error("❌ reportlab not installed. Install with: pip install reportlab")
            return None

        def _escape_for_paragraph(text: Optional[str]) -> str:
            """Safely escape text for reportlab Paragraph"""
            if text is None:
                return ""
            s = str(text)
            s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            s = s.replace('\n', '<br/>')
            return s

        try:
            default_font = 'Helvetica'
            default_bold = 'Helvetica-Bold'
        except Exception:
            default_font = 'Helvetica'
            default_bold = 'Helvetica-Bold'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.export_dir / f"conversation_export_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            str(filename),
            pagesize=letter,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=1.0 * inch,
            bottomMargin=0.8 * inch,
        )

        base_styles = getSampleStyleSheet()

        # Define all styles
        title_style = ParagraphStyle(
            'TitlePremium',
            parent=base_styles['Heading1'],
            fontName=default_bold,
            fontSize=26,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=12,
        )

        subtitle_style = ParagraphStyle(
            'SubtitlePremium',
            parent=base_styles['Normal'],
            fontName=default_font,
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#475569'),
            spaceAfter=18,
        )

        conv_header_style = ParagraphStyle(
            'ConvHeader',
            parent=base_styles['Heading2'],
            fontName=default_bold,
            fontSize=12,
            leading=14,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            'BodyText',
            parent=base_styles['Normal'],
            fontName=default_font,
            fontSize=10.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#0f172a'),
        )

        small_italic = ParagraphStyle(
            'SmallItalic',
            parent=base_styles['Normal'],
            fontName=default_font,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor('#6b7280'),
        )

        # Styles for user and assistant content with backgrounds
        user_content_style = ParagraphStyle(
            'UserContent',
            parent=body_style,
            backColor=colors.HexColor('#f1f5f9'),
            borderColor=colors.HexColor('#e2e8f0'),
            borderWidth=0.5,
            borderPadding=8,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=4,
        )

        assistant_content_style = ParagraphStyle(
            'AssistantContent',
            parent=body_style,
            backColor=colors.HexColor('#eef2ff'),
            borderColor=colors.HexColor('#e2e8f0'),
            borderWidth=0.5,
            borderPadding=8,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=4,
        )

        border_color = colors.HexColor('#e2e8f0')

        def _draw_header(canvas_obj, doc_obj):
            canvas_obj.saveState()
            width, height = doc_obj.pagesize
            header_height = 0.65 * inch
            canvas_obj.setFillColor(colors.HexColor('#4f46e5'))
            canvas_obj.rect(0, height - header_height, width, header_height, stroke=0, fill=1)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.setFont(default_bold, 14)
            canvas_obj.drawString(doc_obj.leftMargin, height - 0.45 * inch, title)
            canvas_obj.setFont(default_font, 8)
            right_meta = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            text_width = canvas_obj.stringWidth(right_meta, default_font, 8)
            canvas_obj.drawString(width - doc_obj.rightMargin - text_width, height - 0.45 * inch, right_meta)
            canvas_obj.restoreState()

        def _draw_footer(canvas_obj, doc_obj):
            canvas_obj.saveState()
            width, _ = doc_obj.pagesize
            footer_y = 0.5 * inch
            canvas_obj.setStrokeColor(border_color)
            canvas_obj.setLineWidth(0.5)
            canvas_obj.line(doc_obj.leftMargin, footer_y + 6, width - doc_obj.rightMargin, footer_y + 6)
            page_num_text = f"Page {canvas_obj.getPageNumber()}"
            canvas_obj.setFont(default_font, 9)
            canvas_obj.setFillColor(colors.HexColor('#6b7280'))
            canvas_obj.drawString(doc_obj.leftMargin, footer_y - 2, page_num_text)
            brand = author if author else 'Generated by Advanced AI Reasoning System Pro'
            brand_width = canvas_obj.stringWidth(brand, default_font, 9)
            canvas_obj.drawString(width - doc_obj.rightMargin - brand_width, footer_y - 2, brand)
            canvas_obj.restoreState()

        def _draw_page(canvas_obj, doc_obj):
            _draw_header(canvas_obj, doc_obj)
            _draw_footer(canvas_obj, doc_obj)

        story = []

        # Cover
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(_escape_for_paragraph(title), title_style))
        if subtitle:
            story.append(Paragraph(_escape_for_paragraph(subtitle), subtitle_style))
        
        meta_lines = []
        meta_lines.append(f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        meta_lines.append(f"<b>Total Conversations:</b> {len(conversations)}")
        if author:
            meta_lines.append(f"<b>Author:</b> {author}")
        story.append(Paragraph(' | '.join(meta_lines), small_italic))
        story.append(Spacer(1, 0.25 * inch))

        # Process each conversation
        for idx, conv in enumerate(conversations, 1):
            # Conversation header
            conv_title = f"Conversation {idx}"
            story.append(Paragraph(_escape_for_paragraph(conv_title), conv_header_style))

            if include_metadata:
                meta_text = (
                    f"<b>Timestamp:</b> {conv.timestamp}   &nbsp;|&nbsp;  "
                    f"<b>Model:</b> {conv.model}   &nbsp;|&nbsp;  "
                    f"<b>Mode:</b> {conv.reasoning_mode}   &nbsp;|&nbsp;  "
                    f"<b>Tokens:</b> {getattr(conv, 'tokens_used', 'N/A')}   &nbsp;|&nbsp;  "
                    f"<b>Time:</b> {getattr(conv, 'inference_time', 0):.2f}s"
                )
                story.append(Paragraph(meta_text, small_italic))
                story.append(Spacer(1, 0.08 * inch))

            # User message - simple paragraph with styling
            story.append(Paragraph('<b>👤 User</b>', body_style))
            story.append(Paragraph(_escape_for_paragraph(conv.user_message), user_content_style))
            story.append(Spacer(1, 0.12 * inch))

            # Assistant response - simple paragraph with styling
            story.append(Paragraph('<b>🤖 Assistant</b>', body_style))
            story.append(Paragraph(_escape_for_paragraph(conv.assistant_response), assistant_content_style))

            # Spacing between conversations
            if idx < len(conversations):
                story.append(Spacer(1, 0.2 * inch))
                story.append(PageBreak())

        # Build the PDF
        doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)

        logger.info(f"✅ PDF exported: {filename}")
        return str(filename)

    
    def export(self, conversations: List[ConversationEntry], 
               format_type: str, include_metadata: bool = True) -> Tuple[str, Optional[str]]:
        """
        📤 UNIFIED EXPORT METHOD
        Returns (content, filepath_string) for Gradio compatibility
        """
        if not conversations:
            return "⚠️ No conversations to export.", None
        
        try:
            if format_type == "json":
                content = self.export_to_json(conversations, include_metadata)
                filename = self._save_to_file(content, "json")
                return content, str(filename)
            
            elif format_type == "markdown":
                content = self.export_to_markdown(conversations, include_metadata)
                filename = self._save_to_file(content, "md")
                return content, str(filename)
            
            elif format_type == "txt":
                content = self.export_to_txt(conversations, include_metadata)
                filename = self._save_to_file(content, "txt")
                return content, str(filename)
            
            elif format_type == "pdf":
                filename = self.export_to_pdf(conversations, include_metadata)
                if filename:
                    return f"✅ PDF exported successfully: {Path(filename).name}", filename
                return "❌ PDF export failed", None
            
            else:
                return f"❌ Unsupported format: {format_type}", None
        
        except Exception as e:
            logger.error(f"❌ Export error: {e}", exc_info=True)
            return f"❌ Export failed: {str(e)}", None
    
    def _save_to_file(self, content: str, extension: str) -> Path:
        """
        💾 SAVE CONTENT TO FILE
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.export_dir / f"conversation_export_{timestamp}.{extension}"
        
        filename.write_text(content, encoding='utf-8')
        logger.info(f"✅ File saved: {filename}")
        return filename
    
    def create_backup(self, conversations: List[ConversationEntry]) -> Optional[str]:
        """
        💾 CREATE AUTOMATIC BACKUP
        Returns string path for Gradio compatibility
        """
        if not conversations:
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.backup_dir / f"backup_{timestamp}.json"
            
            content = self.export_to_json(conversations, include_metadata=True)
            filename.write_text(content, encoding='utf-8')
            
            logger.info(f"✅ Backup created: {filename}")
            return str(filename)
        
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None