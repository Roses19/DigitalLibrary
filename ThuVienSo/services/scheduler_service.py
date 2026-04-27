from apscheduler.schedulers.background import BackgroundScheduler
from ThuVienSo.services.mail_service import run_auto_email_jobs

scheduler = BackgroundScheduler()

def start_scheduler(app):

    def job():
        with app.app_context():
            run_auto_email_jobs()

    # chạy mỗi ngày 8h sáng
    scheduler.add_job(job, 'cron', hour=8, minute=0)

    scheduler.start()