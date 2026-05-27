package com.example.agentknowledge.config;

import com.example.agentknowledge.common.api.TraceContext;
import java.io.IOException;
import java.util.Optional;
import java.util.UUID;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class TraceIdFilter extends OncePerRequestFilter {

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
        try {
            filterChain.doFilter(request, response);
        } finally {
            TraceContext.clear();
        }
    }
}
