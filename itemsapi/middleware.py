class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(f"\nRequest: {request.method} {request.path}")
        print(f"Body: {request.body}")
        
        response = self.get_response(request)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.content}\n")
        return response
