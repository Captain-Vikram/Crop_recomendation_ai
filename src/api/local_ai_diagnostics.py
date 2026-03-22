"""
Local AI Model Status Checker and Diagnostics
Helps verify LM Studio setup and model availability
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class LocalAIDiagnostics:
    """Comprehensive diagnostics for Local AI setup"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234"):
        self.base_url = base_url
        self.diagnostics = {}
    
    def run_full_diagnosis(self) -> Dict[str, Any]:
        """Run full diagnostic suite"""
        self.diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'server_connection': self._check_server(),
            'models': self._check_models(),
            'performance': self._check_performance(),
            'recommendations': self._get_recommendations(),
            'system_status': self._get_system_status()
        }
        return self.diagnostics
    
    def _check_server(self) -> Dict[str, Any]:
        """Check if LM Studio server is running"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                return {
                    'status': 'HEALTHY',
                    'url': self.base_url,
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'message': '✅ LM Studio server is running and responsive'
                }
            else:
                return {
                    'status': 'ERROR',
                    'code': response.status_code,
                    'message': f'❌ Server responded with status {response.status_code}'
                }
        except requests.ConnectionError:
            return {
                'status': 'UNAVAILABLE',
                'message': f'❌ Cannot connect to {self.base_url}',
                'solution': 'Make sure LM Studio server is running'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': f'❌ Connection error: {e}'
            }
    
    def _check_models(self) -> Dict[str, Any]:
        """Check available models"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                models = [m['id'] for m in models_data.get('data', [])]
                
                result = {
                    'status': 'LOADED' if models else 'EMPTY',
                    'count': len(models),
                    'models': models,
                    'details': []
                }
                
                # Get details for each model
                for model_id in models:
                    detail = self._get_model_detail(model_id)
                    is_specialized = self._is_agricultural_model(model_id)
                    result['details'].append({
                        'id': model_id,
                        'type': self._infer_model_type(model_id),
                        'is_specialized': is_specialized,
                        'info': detail
                    })
                
                if not models:
                    result['message'] = '⚠️ No models loaded. Please load a model in LM Studio.'
                else:
                    result['message'] = f'✅ {len(models)} model(s) available'
                
                return result
            else:
                return {
                    'status': 'ERROR',
                    'code': response.status_code,
                    'message': 'Could not fetch models list'
                }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': f'Error checking models: {e}'
            }
    
    def _get_model_detail(self, model_id: str) -> Optional[Dict]:
        """Get details about a specific model"""
        try:
            response = requests.get(f"{self.base_url}/v1/models/{model_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    def _is_agricultural_model(self, model_id: str) -> bool:
        """Check if model is specialized for agriculture"""
        keywords = ['crop', 'agri', 'plant', 'farm', 'soil', 'recommend', 'agriculture']
        return any(kw in model_id.lower() for kw in keywords)
    
    def _infer_model_type(self, model_id: str) -> str:
        """Infer model type from ID"""
        model_lower = model_id.lower()
        if 'llama' in model_lower:
            return 'LLaMA'
        elif 'mistral' in model_lower:
            return 'Mistral'
        elif 'phi' in model_lower:
            return 'Phi'
        else:
            return 'Other'
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check model generation performance"""
        try:
            models_response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if models_response.status_code != 200:
                return {
                    'status': 'SKIPPED',
                    'message': 'Could not fetch models'
                }
            
            models = [m['id'] for m in models_response.json().get('data', [])]
            if not models:
                return {
                    'status': 'SKIPPED',
                    'message': 'No models loaded'
                }
            
            model = models[0]
            
            # Test generation speed
            test_prompt = "Recommend 1 crop for India with water: X liters/week, sunlight: 6-8 hours. Format: JSON"
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an agricultural AI. Respond in JSON format concisely."
                    },
                    {
                        "role": "user",
                        "content": test_prompt
                    }
                ],
                "max_tokens": 200,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                elapsed = response.elapsed.total_seconds()
                return {
                    'status': 'WORKING',
                    'model': model,
                    'generation_time_seconds': round(elapsed, 2),
                    'message': f'✅ Model generating responses (took {elapsed:.2f}s for test)',
                    'speed_assessment': self._assess_speed(elapsed)
                }
            else:
                return {
                    'status': 'ERROR',
                    'code': response.status_code,
                    'message': f'Model failed with status {response.status_code}'
                }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'message': f'Performance check failed: {e}'
            }
    
    def _assess_speed(self, seconds: float) -> str:
        """Assess generation speed quality"""
        if seconds < 5:
            return '⚡ Very Fast'
        elif seconds < 10:
            return '✅ Fast'
        elif seconds < 15:
            return '⚠️ Moderate'
        else:
            return '🐢 Slow (consider using a smaller model)'
    
    def _get_recommendations(self) -> Dict[str, List[str]]:
        """Get recommendations based on diagnostics"""
        recommendations = []
        
        if self.diagnostics['server_connection']['status'] != 'HEALTHY':
            recommendations.append('🔴 Start LM Studio server')
        
        if self.diagnostics['models'].get('status') == 'EMPTY':
            recommendations.append('📥 Load a model in LM Studio')
        elif not any(m.get('is_specialized') for m in self.diagnostics['models'].get('details', [])):
            recommendations.append('🌾 Consider loading llama-3.2-3b-crop-recommender for better agricultural recommendations')
        
        perf = self.diagnostics.get('performance', {})
        if 'slow' in perf.get('speed_assessment', '').lower():
            recommendations.append('⚙️ Consider using a smaller or more optimized model')
        
        return {
            'optimal_setup': len(recommendations) == 0,
            'items': recommendations if recommendations else ['✅ System is optimally configured']
        }
    
    def _get_system_status(self) -> str:
        """Get overall system status"""
        if (self.diagnostics['server_connection']['status'] == 'HEALTHY' and
            self.diagnostics['models'].get('status') == 'LOADED' and
            self.diagnostics['performance'].get('status') == 'WORKING'):
            return '✅ READY'
        elif self.diagnostics['server_connection']['status'] != 'HEALTHY':
            return '❌ OFFLINE'
        elif self.diagnostics['models'].get('status') == 'EMPTY':
            return '⚠️ INCOMPLETE'
        else:
            return '⚠️ PARTIAL'
    
    def print_report(self):
        """Print formatted diagnostic report"""
        d = self.diagnostics
        
        print("\n" + "="*70)
        print(f"LM STUDIO DIAGNOSTICS REPORT - {d['timestamp']}")
        print("="*70)
        
        # Server Status
        print(f"\n🖥️  SERVER STATUS: {d['server_connection']['status']}")
        print(f"   {d['server_connection'].get('message', '')}")
        if 'response_time_ms' in d['server_connection']:
            print(f"   Response time: {d['server_connection']['response_time_ms']:.2f}ms")
        
        # Models
        print(f"\n📦 MODELS: {d['models'].get('message', '')}")
        if d['models'].get('details'):
            for i, model in enumerate(d['models']['details'], 1):
                spec_marker = "🌾" if model['is_specialized'] else "🤖"
                print(f"   {i}. {spec_marker} {model['id']}")
                print(f"      Type: {model['type']}")
                if model['is_specialized']:
                    print(f"      ✅ Specialized for Agriculture")
        
        # Performance
        print(f"\n⚡ PERFORMANCE")
        perf = d.get('performance', {})
        if perf.get('status') == 'WORKING':
            print(f"   {perf.get('message', '')}")
            print(f"   Speed: {perf.get('speed_assessment', '')}")
        elif perf.get('status') == 'SKIPPED':
            print(f"   {perf.get('message', '')}")
        else:
            print(f"   ❌ {perf.get('message', 'Performance check failed')}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        for rec in d['recommendations']['items']:
            print(f"   {rec}")
        
        # Overall Status
        print(f"\n{'='*70}")
        overall = d.get('system_status', 'UNKNOWN')
        status_icon = {
            '✅ READY': '🟢',
            '⚠️ INCOMPLETE': '🟡',
            '❌ OFFLINE': '🔴',
            '⚠️ PARTIAL': '🟡'
        }
        print(f"OVERALL STATUS: {status_icon.get(overall, '⚪')} {overall}")
        print("="*70 + "\n")
    
    def to_json(self) -> str:
        """Export diagnostics as JSON"""
        return json.dumps(self.diagnostics, indent=2, default=str)


def check_local_ai_setup():
    """Quick check of Local AI setup"""
    diagnostics = LocalAIDiagnostics()
    diagnostics.run_full_diagnosis()
    diagnostics.print_report()
    return diagnostics


if __name__ == "__main__":
    # Run diagnostics
    check_local_ai_setup()
