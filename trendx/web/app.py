"""FastAPI web dashboard application."""

from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from ..common.config import settings
from ..common.database import get_session
from ..common.logging import get_logger
from ..common.models import PostQueue, TrendItem, TweetContent

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="TrendX Dashboard",
        description="Dashboard for TrendX trending content curation",
        version="0.1.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    async def dashboard() -> str:
        """Main dashboard page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TrendX Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; }
                .status { padding: 4px 8px; border-radius: 4px; color: white; }
                .status.pending { background-color: #ffc107; }
                .status.posted { background-color: #28a745; }
                .status.failed { background-color: #dc3545; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>TrendX Dashboard</h1>
                
                <div class="card">
                    <h2>Recent Trends</h2>
                    <div id="trends"></div>
                </div>
                
                <div class="card">
                    <h2>Post Queue</h2>
                    <div id="queue"></div>
                </div>
                
                <div class="card">
                    <h2>System Status</h2>
                    <p>Status: <span class="status posted">Running</span></p>
                    <p>Last Update: <span id="lastUpdate"></span></p>
                </div>
            </div>
            
            <script>
                async function loadData() {
                    try {
                        const [trendsResponse, queueResponse] = await Promise.all([
                            fetch('/api/trends'),
                            fetch('/api/queue')
                        ]);
                        
                        const trends = await trendsResponse.json();
                        const queue = await queueResponse.json();
                        
                        document.getElementById('trends').innerHTML = renderTrends(trends);
                        document.getElementById('queue').innerHTML = renderQueue(queue);
                        document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
                    } catch (error) {
                        console.error('Error loading data:', error);
                    }
                }
                
                function renderTrends(trends) {
                    if (trends.length === 0) return '<p>No trends available</p>';
                    
                    return `
                        <table>
                            <tr>
                                <th>Title</th>
                                <th>Source</th>
                                <th>Score</th>
                                <th>Created</th>
                            </tr>
                            ${trends.map(trend => `
                                <tr>
                                    <td>${trend.title}</td>
                                    <td>${trend.source}</td>
                                    <td>${trend.score.toFixed(2)}</td>
                                    <td>${new Date(trend.created_at).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </table>
                    `;
                }
                
                function renderQueue(queue) {
                    if (queue.length === 0) return '<p>No items in queue</p>';
                    
                    return `
                        <table>
                            <tr>
                                <th>Status</th>
                                <th>Scheduled</th>
                                <th>Posted</th>
                                <th>Post ID</th>
                            </tr>
                            ${queue.map(item => `
                                <tr>
                                    <td><span class="status ${item.status}">${item.status}</span></td>
                                    <td>${new Date(item.scheduled_at).toLocaleString()}</td>
                                    <td>${item.posted_at ? new Date(item.posted_at).toLocaleString() : '-'}</td>
                                    <td>${item.twitter_post_id || '-'}</td>
                                </tr>
                            `).join('')}
                        </table>
                    `;
                }
                
                // Load data on page load and refresh every 30 seconds
                loadData();
                setInterval(loadData, 30000);
            </script>
        </body>
        </html>
        """

    @app.get("/api/trends")
    async def get_trends(limit: int = 10) -> List[dict]:
        """Get recent trends."""
        try:
            with get_session() as session:
                trends = session.query(TrendItem).order_by(
                    TrendItem.created_at.desc()
                ).limit(limit).all()

                return [
                    {
                        "id": trend.id,
                        "title": trend.title,
                        "source": trend.source.value,
                        "score": trend.score,
                        "created_at": trend.created_at.isoformat(),
                        "is_turkey_related": trend.is_turkey_related,
                        "is_global": trend.is_global,
                    }
                    for trend in trends
                ]

        except Exception as e:
            logger.error("Error fetching trends", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch trends")

    @app.get("/api/queue")
    async def get_queue(limit: int = 20) -> List[dict]:
        """Get post queue items."""
        try:
            with get_session() as session:
                queue_items = session.query(PostQueue).order_by(
                    PostQueue.scheduled_at.desc()
                ).limit(limit).all()

                return [
                    {
                        "id": item.id,
                        "status": item.status,
                        "scheduled_at": item.scheduled_at.isoformat(),
                        "posted_at": item.posted_at.isoformat() if item.posted_at else None,
                        "twitter_post_id": item.twitter_post_id,
                        "error_message": item.error_message,
                    }
                    for item in queue_items
                ]

        except Exception as e:
            logger.error("Error fetching queue", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to fetch queue")

    @app.get("/api/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.1.0",
        }

    return app
