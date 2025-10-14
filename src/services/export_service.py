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
                     include_metadata: bool = True) -> Optional[str]:
        """
        📄 EXPORT TO PDF (Premium Feature)
        Returns string path for Gradio compatibility
        """
        if not AppConfig.ENABLE_PDF_EXPORT:
            logger.warning("⚠️ PDF export is disabled")
            return None
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
        except ImportError:
            logger.error("❌ reportlab not installed. Install with: pip install reportlab")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.export_dir / f"conversation_export_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(str(filename), pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#667eea',
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Conversation Export", title_style))
        story.append(Paragraph(
            f"<b>Export Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['Normal']
        ))
        story.append(Paragraph(
            f"<b>Total Conversations:</b> {len(conversations)}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Conversations
        for idx, conv in enumerate(conversations, 1):
            story.append(Paragraph(f"<b>Conversation {idx}</b>", styles['Heading2']))
            
            if include_metadata:
                meta_text = (
                    f"<b>Timestamp:</b> {conv.timestamp} | "
                    f"<b>Model:</b> {conv.model} | "
                    f"<b>Mode:</b> {conv.reasoning_mode}<br/>"
                    f"<b>Tokens:</b> {conv.tokens_used} | "
                    f"<b>Time:</b> {conv.inference_time:.2f}s"
                )
                story.append(Paragraph(meta_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>👤 User:</b>", styles['Heading3']))
            story.append(Paragraph(conv.user_message.replace('\n', '<br/>'), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>🤖 Assistant:</b>", styles['Heading3']))
            story.append(Paragraph(conv.assistant_response.replace('\n', '<br/>'), styles['Normal']))
            
            if idx < len(conversations):
                story.append(PageBreak())
        
        doc.build(story)
        logger.info(f"✅ PDF exported: {filename}")
        
        # Return string path for Gradio compatibility
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
                return content, str(filename)  # Convert to string
            
            elif format_type == "markdown":
                content = self.export_to_markdown(conversations, include_metadata)
                filename = self._save_to_file(content, "md")
                return content, str(filename)  # Convert to string
            
            elif format_type == "txt":
                content = self.export_to_txt(conversations, include_metadata)
                filename = self._save_to_file(content, "txt")
                return content, str(filename)  # Convert to string
            
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
            return str(filename)  # Convert to string
        
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None
