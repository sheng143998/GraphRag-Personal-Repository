package com.example.agentknowledge.controller;

import com.example.agentknowledge.common.api.ApiResponse;
import com.example.agentknowledge.common.api.TraceContext;
import com.example.agentknowledge.dto.graph.GraphFactsResponse;
import com.example.agentknowledge.service.GraphFactService;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/graph")
public class GraphFactController {

    private final GraphFactService graphFactService;

    public GraphFactController(GraphFactService graphFactService) {
        this.graphFactService = graphFactService;
    }

    @GetMapping("/facts")
    public ApiResponse<GraphFactsResponse> getFacts(
            @RequestParam UUID knowledgeBaseId,
            @RequestParam(required = false) String entity
    ) {
        return ApiResponse.success(graphFactService.getFacts(knowledgeBaseId, entity), TraceContext.getTraceId());
    }
}
