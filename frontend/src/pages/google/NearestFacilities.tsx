import React, { useState } from 'react';
import { MapPin, Navigation, Search, ExternalLink, Info, Loader2, Hospital } from 'lucide-react';
import { api } from '../../services/api';
import { StateView } from '../../components/common/StateView';
import { useLanguage } from '../../context/LanguageContext';
import { PageHeader } from '../../components/ui/page-header';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '../../components/ui/alert';

interface NearestFacility {
  id: string;
  name: string;
  code: string;
  facility_type: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  straight_line_km: number;
  driving_distance_km?: number | null;
  driving_minutes?: number | null;
}

interface NearestResponse {
  origin_latitude: number;
  origin_longitude: number;
  origin_label?: string | null;
  method: 'google_routes' | 'haversine_only' | string;
  method_note: string;
  facilities: NearestFacility[];
}

type Failure = { status: number; message: string };

const mapsLink = (f: { latitude: number; longitude: number }) =>
  `https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}`;

export default function NearestFacilities() {
  const { t } = useLanguage();
  const [address, setAddress] = useState('');
  const [locating, setLocating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [geoMessage, setGeoMessage] = useState<string | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [result, setResult] = useState<NearestResponse | null>(null);
  const [lastBody, setLastBody] = useState<Record<string, unknown> | null>(null);

  const search = async (body: Record<string, unknown>) => {
    setLoading(true);
    setFailure(null);
    setLastBody(body);
    const res = await api.post<NearestResponse>('/google/maps/nearest-facilities', { limit: 5, ...body });
    setLoading(false);
    if (res.error) {
      setResult(null);
      setFailure({ status: res.error.status, message: res.error.detail });
    } else {
      setResult(res.data);
    }
  };

  const useMyLocation = () => {
    setGeoMessage(null);
    if (!('geolocation' in navigator)) {
      setGeoMessage(t('nearest.geo.unsupported', 'Your browser does not support location. Please type an address or pincode instead.'));
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        void search({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
      },
      (err) => {
        setLocating(false);
        setGeoMessage(
          err.code === err.PERMISSION_DENIED
            ? t('nearest.geo.denied', 'Location permission was denied. You can still type an address or pincode below.')
            : t('nearest.geo.failed', 'We could not determine your location. Please type an address or pincode instead.'),
        );
      },
      { timeout: 15000, maximumAge: 60000 },
    );
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const a = address.trim();
    if (a.length < 3) {
      setGeoMessage(t('nearest.address.short', 'Please enter at least 3 characters.'));
      return;
    }
    setGeoMessage(null);
    void search({ address: a });
  };

  const failureTitle =
    failure?.status === 404
      ? t('nearest.err.notfound', 'Address not found')
      : failure?.status === 503
        ? t('nearest.err.unconfigured', 'Address lookup is not available')
        : undefined;
  const failureMessage =
    failure?.status === 503
      ? t('nearest.err.unconfigured.msg', 'Address search needs Google Maps, which is not configured on this server. Use "Use my location" instead.')
      : failure?.message;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Context-First Standard Page Header */}
      <PageHeader
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: 'Patient Services', href: '/patient' },
          { label: 'Facility Locator' }
        ]}
        scopeBadge={{ label: 'Geo-Spatial Care Grid', variant: 'teal' }}
        roleBadge={{ label: 'Citizen Navigation', variant: 'outline' }}
        title={t('nearest.title', 'Find Nearest Health Facility')}
        description={t('nearest.subtitle', 'Share your location or enter an address or pincode to locate the closest Primary Health Centers and Community Health Centers.')}
      />

      {/* Search & Location Card */}
      <Card className="border-border shadow-xs">
        <CardContent className="p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
            <div>
              <h4 className="text-sm font-bold text-foreground">GPS Location Detection</h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                {t('nearest.geo.why', 'Your location is evaluated once to rank nearby facilities by driving time, and is not stored.')}
              </p>
            </div>
            <Button
              type="button"
              variant="teal"
              size="sm"
              onClick={useMyLocation}
              disabled={locating || loading}
              className="gap-2 text-xs font-semibold shrink-0"
            >
              {locating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Navigation className="w-3.5 h-3.5" />}
              {locating ? t('nearest.locating', 'Detecting GPS...') : t('nearest.use_location', 'Use My Current Location')}
            </Button>
          </div>

          <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-2 pt-1">
            <div className="flex-1 space-y-1">
              <label htmlFor="nearest-address" className="text-xs font-semibold text-foreground">
                {t('nearest.address.label', 'Or type village, town, or 6-digit postal pincode')}
              </label>
              <Input
                id="nearest-address"
                type="text"
                value={address}
                maxLength={300}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={t('nearest.address.placeholder', 'e.g. Chengalpattu, 603001')}
                className="text-xs h-9"
              />
            </div>
            <Button
              type="submit"
              variant="secondary"
              size="sm"
              disabled={loading || locating}
              className="gap-1.5 text-xs h-9 sm:self-end"
            >
              <Search className="w-3.5 h-3.5" />
              {t('nearest.search', 'Search Facilities')}
            </Button>
          </form>

          {geoMessage && (
            <Alert variant="warning" className="text-xs py-2">
              <AlertDescription>{geoMessage}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results View */}
      <div aria-live="polite">
        {loading && <StateView type="loading" message={t('nearest.loading', 'Routing to nearby healthcare facilities...')} />}

        {!loading && failure && (
          <StateView
            type={failure.status === 0 ? 'offline' : 'error'}
            message={failureMessage || failureTitle || 'Could not find nearby facilities.'}
            onRetry={lastBody ? () => void search(lastBody) : undefined}
          />
        )}

        {!loading && !failure && result && (
          <div className="space-y-4">
            {/* Routing Mode Context Banner */}
            <Alert className="border-teal-200 bg-teal-50/70 text-teal-950">
              <Info className="w-4 h-4 text-teal-700" />
              <div className="flex-1">
                <AlertTitle className="text-xs font-bold text-teal-950">
                  {result.method === 'google_routes'
                    ? t('nearest.method.routes', 'Calculated by Road Driving Distance & Traffic')
                    : t('nearest.method.straight', 'Calculated by Straight-Line Distance')}
                </AlertTitle>
                <AlertDescription className="text-xs text-teal-900 mt-0.5">
                  {result.method_note}
                  {result.origin_label && (
                    <span className="font-semibold block mt-0.5">
                      {t('nearest.from', 'Searching from')}: {result.origin_label}
                    </span>
                  )}
                </AlertDescription>
              </div>
            </Alert>

            {result.facilities.length === 0 ? (
              <StateView
                type="empty"
                message={t('nearest.empty.msg', 'No health facilities with registered GPS coordinates were found in this area.')}
              />
            ) : (
              <div className="space-y-3">
                {result.facilities.map((f, i) => (
                  <Card key={f.id} className="border-border shadow-xs hover:border-teal-300 transition-colors">
                    <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="w-5 h-5 rounded-full bg-teal-100 text-teal-800 text-[11px] font-bold flex items-center justify-center">
                            {i + 1}
                          </span>
                          <span className="font-bold text-foreground text-sm">{f.name}</span>
                          <Badge variant="outline" className="text-[10px] font-mono">
                            {f.facility_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {f.district}, {f.state}
                        </p>
                        <div className="text-xs font-medium text-teal-800 pt-0.5">
                          {f.straight_line_km.toFixed(1)} km {t('nearest.straight', 'aerial distance')}
                          {f.driving_distance_km != null && f.driving_minutes != null && (
                            <span className="text-foreground font-bold ml-1">
                              &middot; {f.driving_distance_km.toFixed(1)} km {t('nearest.by_road', 'by road')} (~{Math.round(f.driving_minutes)} {t('nearest.min', 'min drive')})
                            </span>
                          )}
                        </div>
                      </div>

                      <Button
                        variant="outline"
                        size="sm"
                        asChild
                        className="gap-1.5 text-xs border-teal-200 text-teal-800 hover:bg-teal-50 shrink-0 self-start sm:self-auto"
                      >
                        <a
                          href={mapsLink(f)}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`${t('nearest.open_maps', 'Open in Google Maps')}: ${f.name}`}
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          {t('nearest.open_maps', 'Open in Google Maps')}
                        </a>
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
