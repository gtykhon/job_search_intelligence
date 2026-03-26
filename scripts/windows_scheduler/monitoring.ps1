# Job Search Intelligence Monitoring
$LogPath = "C:\path\to\job_search_intelligence\logs"
$ErrorThreshold = 5
$RecentErrors = Get-ChildItem $LogPath -Filter "*error*.log" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }

if ($RecentErrors.Count -gt $ErrorThreshold) {
    # Send alert notification
    $AlertScript = @'
import asyncio
import sys
sys.path.insert(0, r'C:\path\to\job_search_intelligence')

async def send_alert():
    try:
        from src.messaging.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()
        await notifier.send_error_notification(
            'ðŸš¨ **System Alert**: High error rate detected in Job Search Intelligence. Please check logs.'
        )
    except Exception as e:
        print(f'Failed to send alert: {e}')

asyncio.run(send_alert())
'@
    
    $AlertScript | Out-File -FilePath "$LogPath\temp_alert.py" -Encoding UTF8
    python "$LogPath\temp_alert.py"
    Remove-Item "$LogPath\temp_alert.py" -Force
}
