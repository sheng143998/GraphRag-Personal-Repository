package com.example.agentknowledge.config;

import com.example.agentknowledge.common.api.TraceContext;
import java.io.IOException;
import java.util.Optional;
import java.util.UUID;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class TraceIdFilter extends OncePerRequestFilter {

    private static final Logger log = LoggerFactory.getLogger(TraceIdFilter.class);

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        String traceId = Optional.ofNullable(request.getHeader(TraceContext.HEADER_NAME))
                .filter(value -> !value.isBlank())
                .orElse(UUID.randomUUID().toString());

        TraceContext.setTraceId(traceId);
        response.setHeader(TraceContext.HEADER_NAME, traceId);
        long startNanos = System.nanoTime();
        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationMs = (System.nanoTime() - startNanos) / 1_000_000;
            logRequest(request, response, traceId, durationMs);
            TraceContext.clear();
        }
    }

    private void logRequest(HttpServletRequest request, HttpServletResponse response, String traceId, long durationMs) {
        String query = request.getQueryString();
        String path = query == null ? request.getRequestURI() : request.getRequestURI() + "?" + query;
        log.info("接口调用完成: method={}, path={}, status={}, durationMs={}, traceId={}",
                request.getMethod(), path, response.getStatus(), durationMs, traceId);
    }
}
