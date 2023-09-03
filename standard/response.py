class MessageCode:
    INVALID_DATA = "INVALID_DATA"
    UNIQUE_CONSTRAINT = "UNIQUE_CONSTRAINT"
    CLOSED_INCIDENT = "CLOSED_INCIDENT"
    EMAIL_ALREADY_VERIFIED = "EMAIL_ALREADY_VERIFIED"

    INVALID_FILE_TYPE ="INVALID_FILE_TYPE "
    ACCESS_DENIED = "ACCESS_DENIED "
    INVALID_ID = "INVALID_ID"


class ErrorMessage:
    EMAIL_ALREADY_VERIFIED = "already exist this email"
    UNIQUE_CONSTRAINT = "already exist with this field"
    INVALID_ID = "Id Does Not Exist"

    INVALID_FILE_TYPE  = "Invalid file type. Only pptx, docx, and xlsx files are allowed."
    ACCESS_DENIED_UPLOAD = "Access denied. Only Ops Users are allowed to upload files."
    ACCESS_DENIED_DOWNLOAD = "Access denied. Only Client Users are allowed to Download files."


def get_error_response(error_code: str, errors: dict):
    return {"code": error_code, "errors": errors}


