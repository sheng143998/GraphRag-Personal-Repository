package com.example.agentknowledge.common.api;

public record ApiResponse<T>(
        boolean success,
        T data,
        ErrorBody error,
        String traceId
) {
    public static <T> ApiResponse<T> success(T data, String traceId) {
        return new ApiResponse<>(true, data, null, traceId);
    }

    public static <T> ApiResponse<T> failure(String code, String message, String traceId) {
        return new ApiResponse<>(false, null, new ErrorBody(code, message), traceId);
    }

    public record ErrorBody(String code, String message) {
    }
}
