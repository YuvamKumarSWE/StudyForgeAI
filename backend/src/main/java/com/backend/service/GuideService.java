package com.backend.service;

import com.backend.dto.GuideDTO;
import com.backend.dto.GuideRequestDTO;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface GuideService {

    List<GuideDTO> findAll();

    GuideDTO findById(String id);

    GuideDTO save(GuideRequestDTO guideRequestDTO);

    GuideDTO update(String id, GuideRequestDTO guideRequestDTO);

    void deleteById(String id);

    GuideDTO generateAndSave(List<MultipartFile> pdfs, String sourcesJson, Long userId);
}