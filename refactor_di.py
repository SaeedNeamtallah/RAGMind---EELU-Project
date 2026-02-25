import os
from pathlib import Path
import re

def patch_project_controller():
    p = Path(r"backend/controllers/project_controller.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    # 1. Add Depends import (already added in previous step but just in case)
    if "from fastapi import Depends" not in content:
        content = content.replace("import logging", "from fastapi import Depends\nimport logging")
    
    # 2. Update __init__
    content = re.sub(
        r'def __init__\(self\):\s*"""Initialize project controller."""\s*self\.file_service = FileService\(\)',
        'def __init__(self, file_service: FileService = Depends(FileService)):\n        """Initialize project controller."""\n        self.file_service = file_service',
        content
    )
    
    # 3. Update list_projects to return total_count
    # Find list_projects
    old_list = """        try:
            stmt = select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            return list(projects)"""
    new_list = """        try:
            from sqlalchemy import func
            count_stmt = select(func.count()).select_from(Project)
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar()
            
            stmt = select(Project).offset(skip).limit(limit).order_by(Project.created_at.desc())
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            return list(projects), total_count"""
    content = content.replace(old_list, new_list)
    
    p.write_text(content, "utf-8")
    print("Patched project_controller.py")

def patch_document_controller():
    p = Path(r"backend/controllers/document_controller.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    if "from fastapi import Depends" not in content:
        content = content.replace("import logging", "from fastapi import Depends\nimport logging")
        
    old_init = """    def __init__(self):
        \"\"\"Initialize document controller.\"\"\"
        self.file_service = FileService()
        # Lazy imports keep startup fast and avoid circular-import pitfalls.
        from backend.services.document_loader import DocumentLoaderService
        from backend.services.chunking_service import ChunkingService
        from backend.services.embedding_service import EmbeddingService

        self.document_loader = DocumentLoaderService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()"""

    new_init = """    def __init__(self, file_service: FileService = Depends(FileService)):
        \"\"\"Initialize document controller.\"\"\"
        self.file_service = file_service
        # Lazy imports keep startup fast and avoid circular-import pitfalls.
        from backend.services.document_loader import DocumentLoaderService
        from backend.services.chunking_service import ChunkingService
        from backend.services.embedding_service import EmbeddingService

        self.document_loader = DocumentLoaderService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()"""
    
    content = content.replace(old_init, new_init)
    p.write_text(content, "utf-8")
    print("Patched document_controller.py")

def patch_query_controller():
    p = Path(r"backend/controllers/query_controller.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    old_init = """    def __init__(self):
        \"\"\"Initialize query controller.\"\"\"
        # Lazy imports keep startup fast and avoid circular-import pitfalls.
        from backend.services.query_service import QueryService
        from backend.services.answer_service import AnswerService

        self.query_service = QueryService()
        self.answer_service = AnswerService()"""
        
    new_init = """    def __init__(self):
        \"\"\"Initialize query controller.\"\"\"
        # Lazy imports keep startup fast and avoid circular-import pitfalls.
        from backend.services.query_service import QueryService
        from backend.services.answer_service import AnswerService

        self.query_service = QueryService()
        self.answer_service = AnswerService()"""
    # We will skip DI for QueryController for now to avoid circular import complexities with Depends unless requested explicitly. The user specifically pointed to `self.file_service = FileService()`. So let's just stick to FileService in Document/Project controllers, or we can use Depends for AnswerService and QueryService but we'd need to resolve them properly. We'll stick to the specific feedback: `self.file_service = FileService()`. So we skip query_controller for now.
    
def patch_routes_projects():
    p = Path(r"backend/routes/projects.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    old_singleton = """router = APIRouter(prefix="/projects", tags=["Projects"])
_project_controller = None


def get_project_controller() -> ProjectController:
    global _project_controller
    if _project_controller is None:
        _project_controller = ProjectController()
    return _project_controller"""
    
    new_singleton = """router = APIRouter(prefix="/projects", tags=["Projects"])"""
    content = content.replace(old_singleton, new_singleton)
    
    # create_project
    content = re.sub(
        r'async def create_project\(\s*project_data: ProjectCreate,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?(project = await project_controller\.create_project\()',
        r'async def create_project(\n    project_data: ProjectCreate,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """Create a new project."""\n    try:\n        \1',
        content,
        flags=re.DOTALL
    )
    
    # list_projects
    content = re.sub(
        r'async def list_projects\(\s*skip: int = 0,\s*limit: int = 100,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?projects = await project_controller\.list_projects\(db=db, skip=skip, limit=limit\)\s*return projects',
        r'async def list_projects(\n    skip: int = 0,\n    limit: int = 100,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """List all projects."""\n    try:\n        projects, total_count = await project_controller.list_projects(db=db, skip=skip, limit=limit)\n        return {"items": projects, "total_count": total_count}',
        content,
        flags=re.DOTALL
    )
    
    # get_project
    content = re.sub(
        r'async def get_project\(\s*project_id: int,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?(project = await project_controller\.get_project\()',
        r'async def get_project(\n    project_id: int,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """Get project by ID."""\n    try:\n        \1',
        content,
        flags=re.DOTALL
    )
    
    # get_project_stats
    content = re.sub(
        r'async def get_project_stats\(\s*project_id: int,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?(project = await project_controller\.get_project\()',
        r'async def get_project_stats(\n    project_id: int,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """Get project statistics."""\n    try:\n        \1',
        content,
        flags=re.DOTALL
    )
    
    # update_project
    content = re.sub(
        r'async def update_project\(\s*project_id: int,\s*project_data: ProjectUpdate,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?(project = await project_controller\.update_project\()',
        r'async def update_project(\n    project_id: int,\n    project_data: ProjectUpdate,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """Update project."""\n    try:\n        \1',
        content,
        flags=re.DOTALL
    )
    
    # delete_project
    content = re.sub(
        r'async def delete_project\(\s*project_id: int,\s*db: AsyncSession = Depends\(get_db\)\s*\):.*?try:\s*project_controller = get_project_controller\(\).*?(deleted = await project_controller\.delete_project\()',
        r'async def delete_project(\n    project_id: int,\n    db: AsyncSession = Depends(get_db),\n    project_controller: ProjectController = Depends(ProjectController)\n):\n    """Delete project and all associated data."""\n    try:\n        \1',
        content,
        flags=re.DOTALL
    )
    
    p.write_text(content, "utf-8")
    print("Patched projects.py routes")

def patch_routes_documents():
    p = Path(r"backend/routes/documents.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    old_singleton = """router = APIRouter(tags=["Documents"])
_document_controller = None


def get_document_controller() -> DocumentController:
    global _document_controller
    if _document_controller is None:
        _document_controller = DocumentController()
    return _document_controller"""
    
    new_singleton = """router = APIRouter(tags=["Documents"])"""
    content = content.replace(old_singleton, new_singleton)
    
    # Replace document_controller = get_document_controller() with Dependency Injection in params
    content = re.sub(r'async def upload_document\((.*?)\):.*?try:\s*# Read file.*?document_controller = get_document_controller\(\)\s*asset = await document_controller\.upload_document',
        r'async def upload_document(\1,\n    document_controller: DocumentController = Depends(DocumentController)\n):\n    """\n    Upload document to project.\n    Document will be processed in background.\n    """\n    try:\n        # Read file\n        file_content = await file.read()\n        file_size = len(file_content)\n        \n        # Upload document\n        asset = await document_controller.upload_document',
        content, flags=re.DOTALL)
        
    content = re.sub(r'async def list_project_documents\((.*?)\):.*?try:\s*document_controller = get_document_controller\(\)\s*documents = await document_controller\.list_project_documents',
        r'async def list_project_documents(\1,\n    document_controller: DocumentController = Depends(DocumentController)\n):\n    """List all documents in project."""\n    try:\n        documents = await document_controller.list_project_documents',
        content, flags=re.DOTALL)
        
    content = re.sub(r'async def get_document\((.*?)\):.*?try:\s*document_controller = get_document_controller\(\)\s*document = await document_controller\.get_document',
        r'async def get_document(\1,\n    document_controller: DocumentController = Depends(DocumentController)\n):\n    """Get document by ID."""\n    try:\n        document = await document_controller.get_document',
        content, flags=re.DOTALL)
        
    content = re.sub(r'async def process_document\((.*?)\):.*?try:\s*document_controller = get_document_controller\(\)\s*await document_controller\.process_document',
        r'async def process_document(\1,\n    document_controller: DocumentController = Depends(DocumentController)\n):\n    """Manually trigger document processing."""\n    try:\n        await document_controller.process_document',
        content, flags=re.DOTALL)
        
    content = re.sub(r'async def delete_document\((.*?)\):.*?try:\s*document_controller = get_document_controller\(\)\s*deleted = await document_controller\.delete_document',
        r'async def delete_document(\1,\n    document_controller: DocumentController = Depends(DocumentController)\n):\n    """Delete document."""\n    try:\n        deleted = await document_controller.delete_document',
        content, flags=re.DOTALL)

    p.write_text(content, "utf-8")
    print("Patched documents.py routes")

def patch_routes_query():
    p = Path(r"backend/routes/query.py")
    if not p.exists(): return
    content = p.read_text("utf-8")
    
    old_singleton = """router = APIRouter(tags=["Query"])
_query_controller = None


def get_query_controller() -> QueryController:
    global _query_controller
    if _query_controller is None:
        _query_controller = QueryController()
    return _query_controller"""
    
    new_singleton = """router = APIRouter(tags=["Query"])"""
    content = content.replace(old_singleton, new_singleton)
    
    content = re.sub(r'async def query_project\((.*?)\):.*?try:\s*query_controller = get_query_controller\(\)\s*result = await query_controller\.answer_query',
        r'async def query_project(\1,\n    query_controller: QueryController = Depends(QueryController)\n):\n    """\n    Ask a question about project documents.\n    Returns AI-generated answer with sources.\n    """\n    try:\n        result = await query_controller.answer_query',
        content, flags=re.DOTALL)
        
    content = re.sub(r'async def query_project_stream\((.*?)\):.*?"""\n    query_controller = get_query_controller\(\)',
        r'async def query_project_stream(\1,\n    query_controller: QueryController = Depends(QueryController)\n):\n    """\n    Stream an AI-generated answer via Server-Sent Events.\n    Emits: sources event, then token events, then [DONE].\n    """',
        content, flags=re.DOTALL)

    p.write_text(content, "utf-8")
    print("Patched query.py routes")

if __name__ == "__main__":
    import os
    os.chdir(r"c:\\Users\\saeid\\ragmind discussed")
    patch_project_controller()
    patch_document_controller()
    patch_routes_projects()
    patch_routes_documents()
    patch_routes_query()
