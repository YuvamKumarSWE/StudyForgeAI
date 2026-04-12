package com.backend.controller;

import com.backend.dto.GuideDTO;
import com.backend.dto.GuideRequestDTO;
import com.backend.response.ApiResponse;
import com.backend.service.GuideService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/guides")
@RequiredArgsConstructor
@Tag(name = "Guide", description = "Guide management endpoints")
public class GuideController {

    private final GuideService guideService;

    @Operation(summary = "Get all guides")
    @GetMapping
    public ResponseEntity<ApiResponse<List<GuideDTO>>> getAllGuides() {
        List<GuideDTO> guides = guideService.findAll();
        ApiResponse<List<GuideDTO>> response = ApiResponse.success(
                guides,
                "Guides retrieved successfully",
                HttpStatus.OK.value()
        );
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get guide by ID")
    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<GuideDTO>> getGuideById(@PathVariable String id) {
        GuideDTO guide = guideService.findById(id);
        ApiResponse<GuideDTO> response = ApiResponse.success(
                guide,
                "Guide retrieved successfully",
                HttpStatus.OK.value()
        );
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Create a new guide")
    @PostMapping
    public ResponseEntity<ApiResponse<GuideDTO>> createGuide(@Valid @RequestBody GuideRequestDTO guideRequestDTO) {
        GuideDTO guide = guideService.save(guideRequestDTO);
        ApiResponse<GuideDTO> response = ApiResponse.success(
                guide,
                "Guide created successfully",
                HttpStatus.CREATED.value()
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @Operation(summary = "Update guide by ID")
    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<GuideDTO>> updateGuide(
            @PathVariable String id,
            @Valid @RequestBody GuideRequestDTO guideRequestDTO) {
        GuideDTO guide = guideService.update(id, guideRequestDTO);
        ApiResponse<GuideDTO> response = ApiResponse.success(
                guide,
                "Guide updated successfully",
                HttpStatus.OK.value()
        );
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Delete guide by ID")
    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteGuide(@PathVariable String id) {
        guideService.deleteById(id);
        ApiResponse<Void> response = ApiResponse.success(
                null,
                "Guide deleted successfully",
                HttpStatus.OK.value()
        );
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Generate a study guide via AI and save it")
    @PostMapping("/generate")
    public ResponseEntity<ApiResponse<GuideDTO>> generateGuide(
            @RequestPart(value = "pdfs", required = false) List<MultipartFile> pdfs,
            @RequestPart(value = "sources") String sourcesJson,
            @RequestParam(value = "userId", required = false) Long userId) {
        GuideDTO guide = guideService.generateAndSave(pdfs, sourcesJson, userId);
        ApiResponse<GuideDTO> response = ApiResponse.success(
                guide,
                "Study guide generated and saved successfully",
                HttpStatus.CREATED.value()
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}

