import logging
import asyncio
from mbbank import MBBankAsync


async def handle_bank_request_with_retry(func, *args, max_retries=3, initial_delay=5, **kwargs):
    """Handles bank API requests with retry logic for 503 errors"""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if it's a 503 error or content type error
            is_503 = '503' in str(e)
            is_content_type_error = 'mimetype' in str(e) or 'ContentType' in str(e)

            if (is_503 or is_content_type_error) and attempt < max_retries:
                print(
                    f"MBBank API temporarily unavailable (503 error). Retry {attempt}/{max_retries} after {delay}s delay...")
                logging.warning(f"Bank API 503 error, retrying: {str(e)}")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                continue
            raise

    # If we reach here, all retries failed
    raise Exception(f"Failed after {max_retries} attempts to connect to MBBank API")


async def create_bank_client(username, password):
    """Create a new MBBank client instance"""
    try:
        return MBBankAsync(username=username, password=password)
    except Exception as e:
        logging.error(f"Error creating MBBank client: {str(e)}")
        raise