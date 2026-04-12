package com.backend.service.impl;

import com.backend.dto.GuideDTO;
import com.backend.dto.GuideRequestDTO;
import com.backend.exception.DatabaseOperationException;
import com.backend.exception.InvalidRequestException;
import com.backend.exception.ResourceNotFoundException;
import com.backend.mapper.GuideMapper;
import com.backend.model.Guide;
import com.backend.model.User;
import com.backend.repository.GuideRepository;
import com.backend.repository.UserRepository;
import com.backend.service.GuideService;
import com.backend.service.PythonServiceClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional
public class GuideServiceImpl implements GuideService {
    
    private final GuideRepository guideRepository;
    private final GuideMapper guideMapper;
    private final UserRepository userRepository;
    private final PythonServiceClient pythonServiceClient;
    
    @Override
    @Transactional(readOnly = true)
    public List<GuideDTO> findAll() {
        try {
            log.info("Fetching all guides");
            List<Guide> guides = guideRepository.findAll();
            return guides.stream()
                    .map(guideMapper::toDTO)
                    .collect(Collectors.toList());
        } catch (DataAccessException e) {
            log.error("Error fetching all guides", e);
            throw new DatabaseOperationException("Failed to fetch guides", e);
        }
    }
    
    @Override
    @Transactional(readOnly = true)
    public GuideDTO findById(String id) {
        log.info("Fetching guide with id: {}", id);
        Guide guide = guideRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Guide", "id", id));
        return guideMapper.toDTO(guide);
    }
    
    @Override
    public GuideDTO save(GuideRequestDTO guideRequestDTO) {
        log.info("Creating new guide");
        
        
        try {
            Guide guide = guideMapper.toEntity(guideRequestDTO);
            Guide savedGuide = guideRepository.save(guide);
            log.info("Guide created successfully with id: {}", savedGuide.getId());
            
            // If userId is provided, add guide to user's guide list
            if (guideRequestDTO.getUserId() != null) {
                User user = userRepository.findById(guideRequestDTO.getUserId())
                        .orElseThrow(() -> new ResourceNotFoundException("User", "id", guideRequestDTO.getUserId()));
                
                if (!user.getGuideIds().contains(savedGuide.getId())) {
                    user.getGuideIds().add(savedGuide.getId());
                    userRepository.save(user);
                    log.info("Guide added to user's guide list. UserId: {}, GuideId: {}", 
                            user.getId(), savedGuide.getId());
                }
            }
            
            return guideMapper.toDTO(savedGuide);
        } catch (DataAccessException e) {
            log.error("Error saving guide", e);
            throw new DatabaseOperationException("Failed to save guide", e);
        }
    }
    
    @Override
    public GuideDTO update(String id, GuideRequestDTO guideRequestDTO) {
        log.info("Updating guide with id: {}", id);
        
        Guide existingGuide = guideRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Guide", "id", id));
        
        existingGuide.setContent(guideRequestDTO.getContent());
        
        try {
            Guide updatedGuide = guideRepository.save(existingGuide);
            log.info("Guide updated successfully with id: {}", updatedGuide.getId());
            return guideMapper.toDTO(updatedGuide);
        } catch (DataAccessException e) {
            log.error("Error updating guide", e);
            throw new DatabaseOperationException("Failed to update guide", e);
        }
    }
    
    @Override
    public void deleteById(String id) {
        log.info("Deleting guide with id: {}", id);
        
        if (!guideRepository.existsById(id)) {
            throw new ResourceNotFoundException("Guide", "id", id);
        }
        
        try {
            // Remove guide ID from all users who have it
            List<User> usersWithGuide = userRepository.findAll().stream()
                    .filter(user -> user.getGuideIds().contains(id))
                    .collect(Collectors.toList());
            
            for (User user : usersWithGuide) {
                user.getGuideIds().remove(id);
                userRepository.save(user);
                log.info("Removed guide from user's list. UserId: {}, GuideId: {}", user.getId(), id);
            }
            
            guideRepository.deleteById(id);
            log.info("Guide deleted successfully with id: {}", id);
        } catch (DataAccessException e) {
            log.error("Error deleting guide", e);
            throw new DatabaseOperationException("Failed to delete guide", e);
        }
    }

    @Override
    public GuideDTO generateAndSave(List<MultipartFile> pdfs, String sourcesJson, Long userId) {
        log.info("Generating study guide via Python microservice");
        String content = pythonServiceClient.generateStudyGuide(pdfs, sourcesJson);
        GuideRequestDTO guideRequestDTO = new GuideRequestDTO(content, userId);
        return save(guideRequestDTO);
    }
}