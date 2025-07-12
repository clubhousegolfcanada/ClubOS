"""
Phone System Integration for ClubOS
Connects to customer interaction data to learn from real issues
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re

class PhoneSystemService:
    """Service to integrate with phone system customer data"""
    
    def __init__(self):
        self.api_endpoint = os.getenv('PHONE_SYSTEM_API_URL')
        self.api_key = os.getenv('PHONE_SYSTEM_API_KEY')
        self.webhook_secret = os.getenv('PHONE_WEBHOOK_SECRET')
        self.issue_patterns = {}
        self.load_issue_patterns()
    
    def load_issue_patterns(self):
        """Load patterns for extracting issues from call transcripts"""
        self.issue_patterns = {
            'equipment_issues': [
                r'trackman.*(?:not working|broken|error|down)',
                r'projector.*(?:black screen|no image|flickering)',
                r'simulator.*(?:freezing|crashed|slow|lagging)',
                r'screen.*(?:black|blank|distorted|fuzzy)',
                r'computer.*(?:frozen|slow|not responding)'
            ],
            'access_issues': [
                r'(?:can\'t|cannot).*(?:get in|enter|access)',
                r'door.*(?:locked|won\'t open|stuck)',
                r'key.*(?:not working|doesn\'t work)',
                r'card.*(?:not scanning|won\'t read)',
                r'code.*(?:not working|invalid|wrong)'
            ],
            'facility_issues': [
                r'(?:too hot|too cold|temperature)',
                r'lights.*(?:out|not working|dim)',
                r'bathroom.*(?:locked|dirty|broken)',
                r'wifi.*(?:down|slow|not working)',
                r'parking.*(?:full|blocked|lights out)'
            ],
            'billing_issues': [
                r'(?:charged|billed).*(?:wrong|twice|extra)',
                r'refund.*(?:want|need|request)',
                r'payment.*(?:declined|failed|error)',
                r'price.*(?:wrong|different|higher)'
            ],
            'booking_issues': [
                r'reservation.*(?:missing|wrong|cancelled)',
                r'booked.*(?:wrong time|different bay)',
                r'system.*(?:down|not working|slow)',
                r'app.*(?:crashed|error|won\'t load)'
            ]
        }
    
    async def fetch_recent_calls(self, hours: int = 24) -> List[Dict]:
        """Fetch recent customer calls and transcripts"""
        if not self.api_endpoint or not self.api_key:
            print("⚠️  Phone system API not configured")
            return []
        
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Make API request to phone system
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'include_transcripts': True,
                'status': 'completed'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/calls",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                calls = response.json().get('calls', [])
                print(f"📞 Retrieved {len(calls)} calls from phone system")
                return calls
            else:
                print(f"❌ Phone API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching calls: {e}")
            return []
    
    def extract_issues_from_transcript(self, transcript: str) -> List[Dict]:
        """Extract issues from call transcript using pattern matching"""
        if not transcript:
            return []
        
        found_issues = []
        transcript_lower = transcript.lower()
        
        for category, patterns in self.issue_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, transcript_lower, re.IGNORECASE)
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(transcript), match.end() + 50)
                    context = transcript[start:end].strip()
                    
                    found_issues.append({
                        'category': category,
                        'pattern': pattern,
                        'match_text': match.group(),
                        'context': context,
                        'confidence': self.calculate_confidence(match.group(), category)
                    })
        
        return found_issues
    
    def calculate_confidence(self, match_text: str, category: str) -> float:
        """Calculate confidence score for issue detection"""
        base_confidence = 0.7
        
        # Boost confidence for specific equipment mentions
        equipment_terms = ['trackman', 'projector', 'simulator']
        if any(term in match_text.lower() for term in equipment_terms):
            base_confidence += 0.2
        
        # Boost confidence for clear problem indicators
        problem_indicators = ['not working', 'broken', 'error', 'down', 'failed']
        if any(indicator in match_text.lower() for indicator in problem_indicators):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def analyze_customer_issues(self, hours: int = 24) -> Dict:
        """Analyze recent customer issues from phone calls"""
        calls = await self.fetch_recent_calls(hours)
        
        if not calls:
            return {
                'status': 'no_data',
                'message': 'No phone data available'
            }
        
        all_issues = []
        issue_stats = {}
        
        for call in calls:
            transcript = call.get('transcript', '')
            call_issues = self.extract_issues_from_transcript(transcript)
            
            for issue in call_issues:
                issue.update({
                    'call_id': call.get('id'),
                    'call_time': call.get('start_time'),
                    'customer_number': call.get('from_number', 'unknown'),
                    'call_duration': call.get('duration', 0)
                })
                all_issues.append(issue)
                
                # Update stats
                category = issue['category']
                if category not in issue_stats:
                    issue_stats[category] = 0
                issue_stats[category] += 1
        
        # Sort issues by confidence and recency
        all_issues.sort(key=lambda x: (x['confidence'], x['call_time']), reverse=True)
        
        return {
            'status': 'success',
            'total_calls': len(calls),
            'total_issues_detected': len(all_issues),
            'issue_breakdown': issue_stats,
            'top_issues': all_issues[:10],
            'analysis_period': f"{hours} hours",
            'analysis_time': datetime.now().isoformat()
        }
    
    def get_issue_trends(self, days: int = 7) -> Dict:
        """Get trending issues over multiple days"""
        # This would analyze historical data to show trends
        # For now, return mock trending data
        return {
            'trending_up': [
                {'issue': 'trackman_calibration', 'increase': '+25%'},
                {'issue': 'door_access', 'increase': '+15%'}
            ],
            'trending_down': [
                {'issue': 'wifi_problems', 'decrease': '-30%'},
                {'issue': 'billing_issues', 'decrease': '-10%'}
            ],
            'new_issues': [
                {'issue': 'simulator_freezing_bay_3', 'first_seen': '2024-01-15'}
            ]
        }
    
    def create_knowledge_from_calls(self, issues: List[Dict]) -> Dict:
        """Create knowledge base entries from customer call issues"""
        knowledge_entries = {}
        
        # Group issues by category
        for issue in issues:
            category = issue['category']
            if category not in knowledge_entries:
                knowledge_entries[category] = {
                    'common_problems': [],
                    'customer_language': [],
                    'resolution_patterns': []
                }
            
            # Extract how customers describe the problem
            customer_desc = issue['context']
            knowledge_entries[category]['customer_language'].append(customer_desc)
            
            # Extract common problem patterns
            problem = issue['match_text']
            if problem not in knowledge_entries[category]['common_problems']:
                knowledge_entries[category]['common_problems'].append(problem)
        
        return knowledge_entries
    
    async def setup_webhook_listener(self):
        """Setup webhook to receive real-time call data"""
        # This would set up a webhook endpoint to receive real-time call notifications
        # For integration with your phone system's webhook capabilities
        pass
    
    def process_real_time_call(self, call_data: Dict) -> Dict:
        """Process incoming real-time call data"""
        if 'transcript' not in call_data:
            return {'status': 'no_transcript'}
        
        issues = self.extract_issues_from_transcript(call_data['transcript'])
        
        if issues:
            # High-priority issues trigger immediate alerts
            high_priority_issues = [i for i in issues if i['confidence'] > 0.8]
            
            if high_priority_issues:
                return {
                    'status': 'high_priority_issue',
                    'issues': high_priority_issues,
                    'requires_immediate_attention': True,
                    'recommended_action': self.get_recommended_action(high_priority_issues[0])
                }
        
        return {
            'status': 'processed',
            'issues_found': len(issues),
            'issues': issues
        }
    
    def get_recommended_action(self, issue: Dict) -> Dict:
        """Get recommended action for an issue"""
        category = issue['category']
        
        action_map = {
            'equipment_issues': {
                'action': 'dispatch_tech',
                'urgency': 'high',
                'estimated_resolution': '30 minutes'
            },
            'access_issues': {
                'action': 'remote_unlock',
                'urgency': 'immediate',
                'estimated_resolution': '5 minutes'
            },
            'facility_issues': {
                'action': 'facilities_check',
                'urgency': 'medium',
                'estimated_resolution': '1 hour'
            },
            'billing_issues': {
                'action': 'process_refund',
                'urgency': 'low',
                'estimated_resolution': '24 hours'
            }
        }
        
        return action_map.get(category, {
            'action': 'manual_review',
            'urgency': 'medium',
            'estimated_resolution': 'unknown'
        })

# Usage example for ClubOS integration
class PhoneAwareClubOS:
    """ClubOS enhanced with phone system intelligence"""
    
    def __init__(self):
        self.phone_service = PhoneSystemService()
    
    async def get_customer_context(self, issue_description: str) -> Dict:
        """Get context from recent customer calls for similar issues"""
        
        # Analyze recent calls
        call_analysis = await self.phone_service.analyze_customer_issues(hours=48)
        
        if call_analysis['status'] != 'success':
            return {'status': 'no_phone_data'}
        
        # Find similar issues in call data
        similar_issues = []
        for issue in call_analysis['top_issues']:
            if self.is_similar_issue(issue_description, issue['context']):
                similar_issues.append(issue)
        
        return {
            'status': 'found_similar_issues',
            'similar_count': len(similar_issues),
            'customer_descriptions': [i['context'] for i in similar_issues[:3]],
            'confidence_scores': [i['confidence'] for i in similar_issues[:3]],
            'trending_issues': call_analysis['issue_breakdown']
        }
    
    def is_similar_issue(self, description1: str, description2: str) -> bool:
        """Check if two issue descriptions are similar"""
        # Simple similarity check - could be enhanced with NLP
        desc1_words = set(description1.lower().split())
        desc2_words = set(description2.lower().split())
        
        common_words = desc1_words.intersection(desc2_words)
        similarity = len(common_words) / max(len(desc1_words), len(desc2_words))
        
        return similarity > 0.3
